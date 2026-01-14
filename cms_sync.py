import os
import re
import json
import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

OUTPUT_DIR = Path(__file__).parent
TEMPLATE_PATH = OUTPUT_DIR / "_layouts" / "article_template.html" # We will need to create this

def fetch_published_articles():
    """Fetching articles with Status = Published"""
    if not NOTION_TOKEN or not DATABASE_ID:
        print("❌ Error: NOTION_TOKEN or NOTION_DATABASE_ID not found in .env file.")
        return []

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    
    # Payload to filter for Published articles
    # Note: We assume the status property is named "Status" or "状态" and value is "Published" or "已发布"
    # For now, we fetch ALL to inspect structure, then filter in memory or refine query
    payload = {
        "page_size": 100
        # "filter": {
        #     "property": "Status",
        #     "select": {
        #         "equals": "Published"
        #     }
        # }
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"❌ API Request Failed: {e}")
        return []

def fetch_page_blocks(block_id):
    """Fetch all blocks from a page"""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        print(f"❌ Failed to fetch blocks for {block_id}: {e}")
        return []

def blocks_to_html(blocks):
    """Convert Notion blocks to simple HTML"""
    html = []
    
    for block in blocks:
        btype = block["type"]
        
        if btype == "paragraph":
            text = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
            if text:
                html.append(f"<p>{text}</p>")
            else:
                html.append("<br>") # Empty line
                
        elif btype == "heading_1":
            text = "".join([t["plain_text"] for t in block["heading_1"]["rich_text"]])
            html.append(f"<h2>{text}</h2>") # Downgrade H1 to H2 because page title is H1
            
        elif btype == "heading_2":
            text = "".join([t["plain_text"] for t in block["heading_2"]["rich_text"]])
            html.append(f"<h3>{text}</h3>")
            
        elif btype == "heading_3":
            text = "".join([t["plain_text"] for t in block["heading_3"]["rich_text"]])
            html.append(f"<h4>{text}</h4>")
            
        elif btype == "bulleted_list_item":
            text = "".join([t["plain_text"] for t in block["bulleted_list_item"]["rich_text"]])
            html.append(f"<ul><li>{text}</li></ul>") # Simplified list
            
        elif btype == "numbered_list_item":
            text = "".join([t["plain_text"] for t in block["numbered_list_item"]["rich_text"]])
            html.append(f"<ol><li>{text}</li></ol>")
            
        elif btype == "image":
            # Notion image URLs expire after 1 hour!
            # For a robust CMS, we should download them. For now, we use the temporary link 
            # and warn the user, or use valid external URLs if provided.
            img_src = ""
            if block["image"]["type"] == "file":
                img_src = block["image"]["file"]["url"]
            elif block["image"]["type"] == "external":
                img_src = block["image"]["external"]["url"]
            
            if img_src:
                html.append(f'<img src="{img_src}" alt="Notion Image" loading="lazy" style="max-width:100%; border-radius:8px; margin: 1rem 0;">')
                
        elif btype == "quote":
            text = "".join([t["plain_text"] for t in block["quote"]["rich_text"]])
            html.append(f'<blockquote style="border-left: 3px solid var(--hk-red); padding-left: 1rem; color: #ccc; margin: 1.5rem 0;">{text}</blockquote>')

    return "\n".join(html)

    return "\n".join(html)

def get_excerpt(blocks, length=100):
    """Extract excerpt from first paragraph"""
    for block in blocks:
        if block["type"] == "paragraph":
            text = "".join([t["plain_text"] for t in block["paragraph"]["rich_text"]])
            if text:
                return text[:length] + "..." if len(text) > length else text
    return "Click to read more..."

def generate_card_html(article_data, filename, excerpt):
    """Generate HTML for the card in resources.html"""
    tag = article_data['tags'][0] if article_data['tags'] else 'LATEST'
    return f"""
            <!-- Generated Card -->
            <article class="article-card" onclick="location.href='{filename}'">
                <span class="article-tag">{tag}</span>
                <h2 class="article-title">{article_data['title']}</h2>
                <p class="article-excerpt">
                    {excerpt}
                </p>
                <a href="{filename}" class="read-more">Read Insight</a>
            </article>"""

def update_resources_page(cards_html):
    """Inject cards into resources.html"""
    resources_path = OUTPUT_DIR / "resources.html"
    if not resources_path.exists():
        print("❌ resources.html not found!")
        return

    with open(resources_path, "r", encoding="utf-8") as f:
        content = f.read()

    marker_start = "<!-- NOTION_ARTICLES_START -->"
    marker_end = "<!-- NOTION_ARTICLES_END -->"

    if marker_start not in content or marker_end not in content:
        print("❌ Markers not found in resources.html")
        return

    # Replace content between markers
    pattern = re.compile(f"{re.escape(marker_start)}.*{re.escape(marker_end)}", re.DOTALL)
    new_content = pattern.sub(f"{marker_start}\n{cards_html}\n{marker_end}", content)

    with open(resources_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print("✅ Updated resources.html with new articles.")

def update_sitemap(filenames):
    """Add new files to sitemap.xml"""
    sitemap_path = OUTPUT_DIR / "sitemap.xml"
    if not sitemap_path.exists():
        print("⚠️ sitemap.xml not found, skipping update.")
        return

    with open(sitemap_path, "r", encoding="utf-8") as f:
        content = f.readlines()
    
    # Remove closing tag
    new_content = [line for line in content if "</urlset>" not in line]
    
    # Check existing URLs to avoid duplicates
    existing_text = "".join(content)
    base_date = datetime.date.today().isoformat()
    
    added_count = 0
    for filename in filenames:
        if filename in existing_text:
            continue
            
        url_entry = f"""  <url>
    <loc>https://xuanxuan1983.github.io/genius-vision-site/{filename}</loc>
    <lastmod>{base_date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
"""
        new_content.append(url_entry)
        added_count += 1
        
    new_content.append("</urlset>")
    
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.writelines(new_content)
        
    print(f"✅ Added {added_count} new entries to sitemap.xml")
    
def generate_article_html(article_data, content_html, filename):
    """Generate the full HTML file for the article"""
    
    # Simple template
    template = f"""<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{article_data['title']} | GENIUS VISION Insights</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=Noto+Sans+HK:wght@400;700;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {{ --hk-red: #E02020; --bg-black: #050505; --text-main: #FFFFFF; --text-dim: rgba(255, 255, 255, 0.6); --border: rgba(255, 255, 255, 0.1); }}
        body {{ background: var(--bg-black); color: var(--text-main); font-family: 'Inter', 'Noto Sans HK', sans-serif; line-height: 1.8; max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
        h1 {{ font-size: 2.5rem; font-weight: 900; margin-bottom: 2rem; line-height: 1.2; }}
        h2 {{ font-size: 1.8rem; margin: 3rem 0 1.5rem; color: #fff; }}
        h3 {{ font-size: 1.3rem; margin: 2rem 0 1rem; color: var(--hk-red); }}
        p, li {{ margin-bottom: 1.5rem; color: var(--text-dim); font-size: 1.1rem; }}
        strong {{ color: #fff; }}
        ul, ol {{ margin-left: 20px; margin-bottom: 2rem; }}
        .back-link {{ display: inline-flex; align-items: center; gap: 8px; color: var(--hk-red); text-decoration: none; font-weight: 700; margin-bottom: 3rem; text-transform: uppercase; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <a href="resources.html" class="back-link"><i data-lucide="arrow-left"></i> Back to Resources</a>
    
    <span style="color:var(--hk-red); font-weight:900; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; display:block; margin-bottom:10px;">
        {article_data['tags'][0] if article_data['tags'] else 'INSIGHTS'}
    </span>
    
    <h1>{article_data['title']}</h1>
    <p style="font-size:0.9rem; color:#888;">
        发布时间：{article_data['date']} | 阅读时间：约 5 分钟
    </p>
    <hr style="border:0; border-top:1px solid var(--border); margin:2rem 0;">

    <div class="article-content">
        {content_html}
    </div>

    <script>lucide.createIcons();</script>
</body>
</html>"""

    with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
        f.write(template)
    
    print(f"✅ Generated: {{filename}}")


def search_databases():
    """List all databases shared with the integration"""
    url = "https://api.notion.com/v1/search"
    payload = {
        "filter": {
            "value": "database",
            "property": "object"
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        print(f"❌ Search Failed: {e}")
        return []

def extract_property(page, prop_name, default=""):
    """Helper to safely extract Notion properties"""
    props = page.get("properties", {})
    
    # Try finding the property case-insensitively
    target_key = None
    for key in props.keys():
        if key.lower() == prop_name.lower():
            target_key = key
            break
    
    if not target_key:
        return default
        
    prop_data = props[target_key]
    prop_type = prop_data.get("type")
    
    if prop_type == "title":
        return prop_data["title"][0]["plain_text"] if prop_data["title"] else default
    elif prop_type == "rich_text":
        return prop_data["rich_text"][0]["plain_text"] if prop_data["rich_text"] else default
    elif prop_type == "select":
        return prop_data["select"]["name"] if prop_data["select"] else default
    elif prop_type == "multi_select":
        return [tag["name"] for tag in prop_data["multi_select"]]
    elif prop_type == "date":
        return prop_data["date"]["start"] if prop_data["date"] else default
    elif prop_type == "url":
        return prop_data["url"]
    
    return default

def main():
    print("🔄 Connecting to Notion...")

    # If no database ID is configured, list available databases
    if not DATABASE_ID or "your_database_id_here" in DATABASE_ID:
        print("⚠️ No Database ID configured in .env. Searching for accessible databases...")
        dbs = search_databases()
        if not dbs:
            print("❌ No databases found. Please make sure you have shared your database with the 'Genius Vision Site' integration.")
            return
        
        print("\n✅ Found the following databases:")
        for db in dbs:
            title = extract_property(db, "title", "Untitled")
            # For databases, title is in "title" property but structure is different, usually it's "title" key in the db object itself
            # The 'extract_property' helper is for pages. Let's handle DB title manually
            try:
                if "title" in db and db["title"]:
                    title = db["title"][0]["plain_text"]
                else:
                    title = "Untitled"
            except:
                title = "Unknown"
                
            print(f"   PLEASE COPY THIS ID -> [{db['id']}] : {title}")
            
        print("\n👇 Action: Copy the ID above and paste it into your .env file as NOTION_DATABASE_ID")
        return


    articles = fetch_published_articles()
    
    if not articles:
        print("⚠️ No articles found or connection failed.")
        return

    print(f"✅ Found {len(articles)} items in database.")
    
    print(f"✅ Found {len(articles)} items in database.")
    
    generated_cards = []

    # Process each article
    for page in articles:
        # 1. Map Properties
        title = extract_property(page, "名称", "Untitled")
        date = extract_property(page, "发布时间", datetime.date.today().isoformat())
        status = extract_property(page, "文章状态", "Draft")
        tags = extract_property(page, "内容类型", [])
        
        # 2. Filter 
        # Only process '发布', '已发布' or 'Published'
        if status not in ["发布", "已发布", "Published"]:
            print(f"Skipping: {title} [{status}]")
            continue
            
        print(f"Processing: {title} [{status}]")

        # 3. Generate Filename (using ID for safety)
        safe_title = re.sub(r'[^a-zA-Z0-9]', '', title)[:20] 
        filename = f"article-{page['id'].replace('-', '')[:12]}.html"
        
        # 4. Fetch Content
        blocks = fetch_page_blocks(page["id"])
        content_html = blocks_to_html(blocks)
        excerpt = get_excerpt(blocks)
        
        # 5. Generate HTML File
        article_data = {
            "title": title,
            "date": date,
            "tags": tags
        }
        generate_article_html(article_data, content_html, filename)
        
        # 6. Generate Card HTML
        generated_cards.append(generate_card_html(article_data, filename, excerpt))
        
    # Update resources.html
    if generated_cards:
        update_resources_page("\n".join(generated_cards))
        
        # Update Sitemap
        new_filenames = [card.split("href='")[1].split("'")[0] for card in generated_cards]
        update_sitemap(new_filenames)
        
    print("\n🎉 Sync Complete! Check the generated .html files.")


if __name__ == "__main__":
    main()
