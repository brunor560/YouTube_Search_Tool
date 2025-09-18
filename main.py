""" This program will create a script that searches through the use of the YouTube API to
give the user information of different education videos using hashtags to filter
the topics. The user can also filter the videos based on the prefered language."""

import csv
from googleapiclient.discovery import build

key = #ENTER YOUR OWN API KEY
per_hashtag = 50        # maximum api call for YT is 50
total = 100             # 100 is what we need for the challenge
oFile = "educational_video_list.csv"


youtube = build("youtube", "v3", developerKey=key)

def fetch_videos_for_hashtag(hashtag, max_results, lang=None):
    videos = []
    next_page_token = None

    while len(videos) < max_results:
        request = youtube.search().list(
            q=hashtag,
            part="snippet",
            type="video",
            relevanceLanguage = lang if lang else None,
            maxResults=min(50, max_results - len(videos)),
            pageToken=next_page_token
        )
        response = request.execute()

        video_ids = [item['id']['videoId'] for item in response['items']]

        # Get the stats for views and likes
        stats_request = youtube.videos().list(
            part="snippet, statistics",
            id=",".join(video_ids)
        )
        stats_response = stats_request.execute()
        stats_map = {item['id']: item for item in stats_response['items']}

        for item in response['items']:
            vid = item['id']['videoId']
            snippet = stats_map[vid]['snippet']
            statistics = stats_map[vid]['statistics']

            combined_text = (snippet.get('title', '') + ' ' + snippet.get('description', ''))

            # Makes sure the hashtag is present (not just similar words)
            if hashtag.lower() not in combined_text.lower():
                continue

            language = snippet.get('defaultAudioLanguage') or snippet.get('defaultLanguage')
            if lang and language and language.lower() != lang.lower():
                continue

            videos.append({
                "hashtag": hashtag,
                "video_id": vid,
                "title": snippet.get('title', ''),
                "description": snippet.get('description', ''),
                "channel_title": snippet.get('channelTitle', ''),
                "publish_date": snippet.get('publishedAt', ''),
                "view_count": statistics.get('viewCount', '0'),
                "like_count": statistics.get('likeCount', '0'),
                # "dislike_count": stats_map.get(vid, {}).get('dislikeCount', '0'),
                    # YouTube removed dislike count but could've been useful to have

            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos

def main():
    # User interface, asks for the hashtag inputs
    raw_input = input(
        "Enter one or more hashtags separated by spaces (include or leave out the #):\n"
    )
    hashtags = []
    for h in raw_input.split():
        h = h.strip()
        if not h:
            continue
        if not h.startswith("#"):
            h = "#" + h
        hashtags.append(h)

    if not hashtags:
        print("No hashtags entered. Exiting.")
        return

    # User interface, asks for the users perfered language, will only present videos in that language
    lang = input(
        "Enter a language code (en for English, fr for French, etc.):\n"
        "If left blank, it'll search all languages:\n"
    ).strip()
    if lang and len(lang) != 2:
        print("Invalid language code. Searching all languages...")
        lang = None

    print(f"\nSearching YouTube for hashtags: {', '.join(hashtags)}"
        f"{' with language code '+lang if lang else ''}\n")

    # Presents the results found
    all_results = []
    per_hashtag_target = max(total // len(hashtags), per_hashtag)
    for h in hashtags:
        results = fetch_videos_for_hashtag(h, per_hashtag_target)
        print(f"Found {len(results)} videos for {h}")
        all_results.extend(results)

    # Saves the list into a csv file
    with open(oFile, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["hashtag", "video_id", "title", "description",
                        "channel_title", "publish_date",
                        "view_count", "like_count"] #"dislike_count"
        )
        writer.writeheader()
        writer.writerows(all_results)

    print(f"\nSaved {len(all_results)} videos to {oFile}")

if __name__ == "__main__":
    main()
