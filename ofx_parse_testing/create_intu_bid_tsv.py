import urllib.request
import csv

# Intuit's live production directories
urls = [
    "https://ofx-prod-filist.intuit.com/qw2800-can/data/fidir-c.txt",  # Canadian
    "https://ofx-prod-filist.intuit.com/qb3400/data/fidir.txt"         # US
]

bank_map = {}

print("Downloading and parsing Intuit FIDIR files...")

for url in urls:
    try:
        # User-Agent is added to prevent the request from being blocked
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8', errors='ignore')
            
            for line in content.splitlines():
                parts = line.split('\t')
                
                # Check if line has enough columns and starts with a numeric BID
                if len(parts) >= 4 and parts[0].strip().isdigit():
                    bid = parts[0].strip()
                    name = parts[3].strip() # Canadian file has the names on the 3rd column
                    if name.isdigit(): # Handle the exception of the US file where the names are the 4th column
                        name = parts[4].strip()
                    bank_map[bid] = name
                    
    except Exception as e:
        print(f"Error fetching {url}: {e}")

# Save to a TSV file
output_path = 'intu_bid_lookup.tsv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter='\t')
    writer.writerow(['INTU.BID', 'Bank Name'])
    
    # Sort numerically by BID for a clean file
    for bid, name in sorted(bank_map.items(), key=lambda x: int(x[0])):
        writer.writerow([bid, name])

print(f"Success! Generated '{output_path}' with {len(bank_map)} bank entries.")