import urllib.request
import json
import os
import asyncio
from datetime import datetime
import sys

async def fetch_archive_mirror_url(version_filename):
    if "spotify_installer-" not in version_filename:
        return None
        
    base_ver = version_filename.replace("spotify_installer-", "").replace("-x64.exe", "")
    base_ver = base_ver.rsplit("-", 1)[0] if "-" in base_ver else base_ver
    
    search_prefix = f"spotify_installer-{base_ver}"
    archive_url = "https://archive.org/download/spotify-installer-museum/windows/x86_64/exe/"
    
    import aiohttp
    import re
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
            headers = {"User-Agent": "Spicetify-EasyInstall"}
            async with session.get(archive_url, headers=headers) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    links = re.findall(r'href=[\'\"]?([^\'\" >]+)', html)
                    for link in links:
                        if search_prefix in link and link.endswith(".exe"):
                            print(f"Archive mirror found: {archive_url + link}")
                            return archive_url + link
                else:
                    return ""
    except Exception as e:
        print(f"Archive lookup error: {e}")
    return ""

def fetch_json(url, headers=None):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Failed fetching {url}: {e}")
        return None

async def update_spotify_presets():
    print("Updating spotify_presets.json...")
    data = fetch_json("https://loadspot.pages.dev/versions.json")
    if not data:
        return None
        
    try:
        with open("resources/data/spotify_presets.json", "r", encoding="utf-8") as f:
            old_presets = json.load(f)
    except Exception:
        old_presets = {}
        
    presets = {}
    seen_major_vers = set()
    
    for ver, info in data.items():
        if "win" not in info:
            continue
            
        x64_dict = info["win"].get("x64")
        x86_dict = info["win"].get("x86")
        
        if not x64_dict and not x86_dict:
            continue
            
        if x64_dict:
            url_x64 = x64_dict.get("url", "")
            url_x86 = x86_dict.get("url", "") if x86_dict else ""
            raw_date = x64_dict.get("date", "")
        else:
            # Fallback for very old versions where LoadSpot only lists x86 in JSON
            url_x86 = x86_dict.get("url", "")
            url_x64 = url_x86.replace("-x86.exe", "-x64.exe")
            raw_date = x86_dict.get("date", "")
        
        if not url_x64 or not raw_date:
            continue
            
        # Extract filename (e.g., spotify_installer-1.2.92.148.g882cc571-x64.exe)
        filename_x64 = url_x64.split('/')[-1]
        filename_x86 = url_x86.split('/')[-1] if url_x86 else ""
        
        # We need the fullversion string, typically something like "1.2.92.148.g882cc571"
        version_str = filename_x64.replace("spotify_installer-", "").replace("-x64.exe", "")
        if not version_str:
            continue
            
        # The date is usually DD.MM.YYYY, but we want YYYY-MM-DD
        date_parts = raw_date.split('.')
        if len(date_parts) == 3:
            iso_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
        else:
            iso_date = raw_date
            
        # Major version string like "1.2.92"
        major_parts = ver.split('.')
        if len(major_parts) >= 3:
            major_ver = f"{major_parts[0]}.{major_parts[1]}.{major_parts[2]}"
            
            if major_ver in seen_major_vers:
                continue
            seen_major_vers.add(major_ver)
            
            key = f"{major_ver} ({iso_date})"
            
            if key in old_presets and "archive_url" in old_presets[key] and old_presets[key]["archive_url"]:
                presets[key] = old_presets[key]
                continue
            
            print(f"Resolving mirror for {key}...")
            # We must use async archive mirror lookup just like the user's golden thread
            archive_x64 = await fetch_archive_mirror_url(filename_x64)
            archive_x86 = await fetch_archive_mirror_url(filename_x86) if filename_x86 else ""
            
            presets[key] = {
                "version": version_str,
                "loadspot_url": url_x64,
                "archive_url": archive_x64 or f"https://web.archive.org/web/2/{url_x64}",
                "loadspot_url_x86": url_x86,
                "archive_url_x86": archive_x86 or (f"https://web.archive.org/web/2/{url_x86}" if url_x86 else "")
            }
            
    return presets

def fetch_spicetify_data():
    print("Updating shipped_shas.json and spicetify_dates.json...")
    token = os.environ.get("GITHUB_TOKEN")
    headers = {'User-Agent': 'Mozilla/5.0'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
        
    releases = []
    page = 1
    while True:
        page_releases = fetch_json(f"https://api.github.com/repos/spicetify/spicetify-cli/releases?per_page=100&page={page}", headers)
        if not page_releases:
            break
        releases.extend(page_releases)
        if len(page_releases) < 100:
            break
        page += 1
        
    if not releases:
        return None, None
        
    shas = {}
    dates = {"Latest": ""}
    
    for rel in releases:
        tag = rel["tag_name"].lstrip('v')
        published_at = rel["published_at"]
        date_only = published_at.split("T")[0]
        
        dates[tag] = date_only
        
        # This will get heavily rate-limited unauthenticated, but fine in Action
        cli_commits = fetch_json(f"https://api.github.com/repos/spicetify/spicetify-cli/commits?until={published_at}&per_page=1", headers)
        theme_commits = fetch_json(f"https://api.github.com/repos/spicetify/spicetify-themes/commits?until={published_at}&per_page=1", headers)
        
        if cli_commits and theme_commits and len(cli_commits) > 0 and len(theme_commits) > 0:
            shas[tag] = {
                "cli": cli_commits[0]["sha"],
                "themes": theme_commits[0]["sha"]
            }
            
    return shas, dates

async def main():
    presets = await update_spotify_presets()
    if presets:
        with open("resources/data/spotify_presets.json", "w", encoding="utf-8") as f:
            json.dump(presets, f, indent=4)
            print("Successfully updated spotify_presets.json")
            
    shas, dates = fetch_spicetify_data()
    if shas and dates:
        with open("resources/data/shipped_shas.json", "w", encoding="utf-8") as f:
            json.dump(shas, f, indent=4)
            print("Successfully updated shipped_shas.json")
        with open("resources/data/spicetify_dates.json", "w", encoding="utf-8") as f:
            json.dump(dates, f, indent=4)
            print("Successfully updated spicetify_dates.json")

if __name__ == "__main__":
    asyncio.run(main())
