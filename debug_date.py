import frontmatter
import datetime
import os
import config

file_path = "/Users/kory/_vault/_notes/_articles/Free_speechs_great_leap_backwards.md"
today_str = datetime.date.today().strftime("%Y-%m-%d")

print(f"Checking file: {file_path}")
print(f"Today string: '{today_str}'")

if os.path.exists(file_path):
    post = frontmatter.load(file_path)
    date_val = post.get('date')
    print(f"Raw date value: {repr(date_val)}")
    print(f"Type of date value: {type(date_val)}")
    print(f"String converted: '{str(date_val)}'")
    
    if str(date_val) == today_str:
        print("MATCH!")
    else:
        print("NO MATCH")
else:
    print("File not found")

print(f"Config Articles Dir: {config.ARTICLES_DIR}")
print(f"Files in Dir: {len(os.listdir(config.ARTICLES_DIR))}")
