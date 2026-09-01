#!/usr/bin/env python3
"""Validate sitemap structure and content."""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

WEB = Path(__file__).parent / "web"
SITE = "https://watchwiththekids.com"

def validate_sitemap_index():
    """Validate main sitemap index."""
    sitemap_path = WEB / "sitemap.xml"
    if not sitemap_path.exists():
        print("❌ sitemap.xml not found")
        return False
    
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        
        # Check it's a sitemapindex
        if not root.tag.endswith('sitemapindex'):
            print(f"❌ Root element should be sitemapindex, got {root.tag}")
            return False
        
        # Get all child sitemaps
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemaps = root.findall('sm:sitemap', ns)
        
        if len(sitemaps) == 0:
            print("❌ No child sitemaps found in index")
            return False
        
        print(f"✅ Sitemap index valid with {len(sitemaps)} child sitemaps:")
        for sitemap in sitemaps:
            loc = sitemap.find('sm:loc', ns)
            lastmod = sitemap.find('sm:lastmod', ns)
            if loc is not None:
                filename = loc.text.split('/')[-1]
                date = lastmod.text if lastmod is not None else "no date"
                print(f"   - {filename} (lastmod: {date})")
        
        return True
    except ET.ParseError as e:
        print(f"❌ XML parse error: {e}")
        return False

def validate_child_sitemaps():
    """Validate all child sitemap files."""
    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap_files = sorted(WEB.glob("sitemap-*.xml"))
    
    if not sitemap_files:
        print("❌ No child sitemap files found")
        return False
    
    print(f"\n✅ Found {len(sitemap_files)} child sitemap files:")
    
    total_urls = 0
    for sitemap_path in sitemap_files:
        try:
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            
            if not root.tag.endswith('urlset'):
                print(f"❌ {sitemap_path.name}: Should be urlset, got {root.tag}")
                continue
            
            urls = root.findall('sm:url', ns)
            total_urls += len(urls)
            
            # Check first URL structure
            if urls:
                first_url = urls[0]
                loc = first_url.find('sm:loc', ns)
                lastmod = first_url.find('sm:lastmod', ns)
                priority = first_url.find('sm:priority', ns)
                
                if loc is None or not loc.text.startswith(SITE):
                    print(f"❌ {sitemap_path.name}: Invalid URL structure")
                    continue
            
            print(f"   ✅ {sitemap_path.name}: {len(urls)} URLs")
        except ET.ParseError as e:
            print(f"❌ {sitemap_path.name}: XML parse error: {e}")
            return False
    
    print(f"\n✅ Total URLs across all sitemaps: {total_urls}")
    return total_urls > 0

def validate_robots_txt():
    """Validate robots.txt points to sitemap."""
    robots_path = WEB / "robots.txt"
    if not robots_path.exists():
        print("❌ robots.txt not found")
        return False
    
    content = robots_path.read_text()
    expected = f"Sitemap: {SITE}/sitemap.xml"
    
    if expected in content:
        print(f"\n✅ robots.txt correctly points to sitemap")
        return True
    else:
        print(f"❌ robots.txt missing or incorrect sitemap reference")
        return False

def main():
    print("🔍 Validating sitemap structure...\n")
    
    results = [
        validate_sitemap_index(),
        validate_child_sitemaps(),
        validate_robots_txt(),
    ]
    
    if all(results):
        print("\n✅ All sitemap validations passed!")
        return 0
    else:
        print("\n❌ Some validations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
