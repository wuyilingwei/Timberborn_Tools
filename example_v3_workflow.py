"""
Example demonstration of v3 workflow
This shows how the tool processes mod data
"""
import os
import tempfile
import csv
from collections import OrderedDict
import toml
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.file_v3 import TomlFile

def create_sample_mod_csv(csv_path):
    """Create a sample mod CSV file"""
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Text', 'Comment'])
        writer.writerow(['KnatteTobbert.MetalStaircase.DisplayName', 'Metal Stairs', ''])
        writer.writerow(['KnatteTobbert.MetalStaircase.Description', 'A durable metal staircase', ''])
        writer.writerow(['KnatteTobbert.WoodenDoor.DisplayName', 'Wooden Door', ''])

def create_existing_toml(toml_path):
    """Create an existing TOML file (simulating previous run)"""
    data = OrderedDict()
    data['name'] = 'Metal Staircase Mod'
    data['KnatteTobbert.MetalStaircase.DisplayName'] = OrderedDict([
        ('raw', 'Metal Stairs'),
        ('enUS', 'Metal Stairs'),
        ('zhCN', '金属楼梯'),
        ('zhTW', '金屬樓梯'),
    ])
    data['KnatteTobbert.MetalStaircase.Description'] = OrderedDict([
        ('raw', 'A metal staircase'),  # Note: This will be detected as changed
        ('enUS', 'A metal staircase'),
        ('zhCN', '金属楼梯'),
    ])
    # WoodenDoor is new, not in existing TOML
    
    with open(toml_path, 'w', encoding='utf-8') as f:
        toml.dump(data, f)

def main():
    print("=" * 80)
    print("V3 Workflow Example")
    print("=" * 80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        csv_path = os.path.join(tmpdir, "mod_en.csv")
        old_toml_path = os.path.join(tmpdir, "3275060459_version-0.6.toml")
        output_dir = os.path.join(tmpdir, "output")
        os.makedirs(output_dir)
        
        print("\n1. Creating sample mod CSV file (simulating mod download)...")
        create_sample_mod_csv(csv_path)
        print("   ✓ Created mod CSV with 3 entries")
        
        print("\n2. Creating existing TOML file (simulating previous run)...")
        create_existing_toml(old_toml_path)
        print("   ✓ Created existing TOML with 2 entries (one will be outdated)")
        
        print("\n3. Processing with v3 tool...")
        toml_file = TomlFile(
            mod_id="3275060459",
            mod_name="Metal Staircase Mod v2",
            raw_csv_path=csv_path
        )
        toml_file.process(old_toml_path, output_dir, "3275060459_version-0.6")
        print("   ✓ Processing complete")
        
        print("\n4. Results:")
        print("-" * 80)
        
        output_path = os.path.join(output_dir, "3275060459_version-0.6.toml")
        with open(output_path, 'r', encoding='utf-8') as f:
            result = toml.load(f, _dict=OrderedDict)
        
        print("\nGenerated TOML:")
        print(toml.dumps(result))
        
        print("\n5. Analysis:")
        print("-" * 80)
        
        # Check name
        if result['name'] == 'Metal Staircase Mod v2':
            print("✓ Mod name updated from 'Metal Staircase Mod' to 'Metal Staircase Mod v2'")
        
        # Check DisplayName (unchanged)
        display_name = result['KnatteTobbert.MetalStaircase.DisplayName']
        if 'new' not in display_name:
            print("✓ DisplayName unchanged - kept all translations without 'new' field")
        
        # Check Description (changed)
        description = result['KnatteTobbert.MetalStaircase.Description']
        if 'new' in description:
            print(f"✓ Description changed:")
            print(f"    Old: '{description['raw']}'")
            print(f"    New: '{description['new']}'")
            print(f"    → Cloud workflow will retranslate")
        
        # Check WoodenDoor (new)
        wooden_door = result['KnatteTobbert.WoodenDoor.DisplayName']
        if 'new' in wooden_door and 'raw' not in wooden_door:
            print(f"✓ WoodenDoor is new entry:")
            print(f"    New: '{wooden_door['new']}'")
            print(f"    → Cloud workflow will translate for first time")
        
        print("\n" + "=" * 80)
        print("Example complete!")
        print("=" * 80)
        print("\nNext steps in cloud workflow:")
        print("1. Detect entries with 'new' field")
        print("2. Translate 'new' values to all target languages")
        print("3. For changed entries: update 'raw' and all language fields")
        print("4. For new entries: add 'raw' and all language fields")
        print("5. Remove 'new' field")
        print("6. Publish to mod repository")

if __name__ == '__main__':
    main()
