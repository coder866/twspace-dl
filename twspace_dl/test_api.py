#!/usr/bin/env python3
# test_api_simple.py
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import json
import logging

logging.basicConfig(level=logging.DEBUG)


# Manually load cookies from your cookie file
def load_cookies_from_file(cookie_file):
    """Simple cookie loader for testing"""
    cookies = {}
    try:
        with open(cookie_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 7:
                    domain, flag, path, secure, expiration, name, value = parts[:7]
                    cookies[name] = value
    except Exception as e:
        print(f"Error loading cookies: {e}")
    return cookies


def main():
    if len(sys.argv) < 3:
        print("Usage: python test_api_simple.py <cookie_file> <space_id>")
        print("Example: python test_api_simple.py cookies.txt 1yNGabkPQqNJj")
        sys.exit(1)

    cookie_file = sys.argv[1]
    space_id = sys.argv[2]

    print(f"Testing with space ID: {space_id}")

    # Load cookies
    cookies = load_cookies_from_file(cookie_file)
    print(f"Loaded {len(cookies)} cookies")

    if "ct0" not in cookies:
        print("ERROR: ct0 cookie not found! This is required for authentication.")
        print(f"Available cookies: {list(cookies.keys())}")
        sys.exit(1)

    # Build the URL
    variables = {
        "id": space_id,
        "isMetatagsQuery": False,
        "withReplays": True,
        "withListeners": True,
    }

    features = (
        '{"spaces_2022_h2_spaces_communities":true,"spaces_2022_h2_clipping":true,'
        '"creator_subscriptions_tweet_preview_api_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,'
        '"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,'
        '"verified_phone_label_enabled":false,"premium_content_api_read_enabled":false,'
        '"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,'
        '"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,'
        '"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,'
        '"articles_preview_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,'
        '"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,'
        '"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,'
        '"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,'
        '"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,'
        '"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,'
        '"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,'
        '"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,'
        '"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,'
        '"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,'
        '"responsive_web_enhance_cards_enabled":false}'
    )

    # URL encode
    import urllib.parse

    encoded_vars = urllib.parse.quote(json.dumps(variables, separators=(",", ":")))
    encoded_features = urllib.parse.quote(features)

    url = f"https://x.com/i/api/graphql/rC2zlE1t7SHbVG8obPZliQ/AudioSpaceById?variables={encoded_vars}&features={encoded_features}"

    print(f"\nRequest URL: {url[:200]}...")

    # Headers - IMPORTANT: Don't accept brotli
    headers = {
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "x-csrf-token": cookies.get("ct0", ""),
        "content-type": "application/json",
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "accept": "*/*",
        # CRITICAL: Don't accept brotli to avoid decompression issues
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,en;q=0.9",
        "dnt": "1",
        "priority": "u=1, i",
        "sec-ch-ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "origin": "https://x.com",
        "referer": "https://x.com/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    }

    print("\nMaking request...")
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)

        print(f"\n=== RESPONSE ===")
        print(f"Status: {response.status_code}")
        print(f"Content-Encoding: {response.headers.get('content-encoding')}")
        print(f"Content-Length: {len(response.content)} bytes")
        print(f"Content-Type: {response.headers.get('content-type')}")

        # Save raw response for debugging
        with open(f"response_raw_{space_id}.bin", "wb") as f:
            f.write(response.content)
        print(f"Saved raw response to response_raw_{space_id}.bin")

        # Check if we got a response
        if not response.content:
            print("ERROR: Empty response!")
            return

        # Check if it looks like binary
        first_byte = response.content[0] if response.content else None
        print(f"First byte (decimal): {first_byte}")
        print(
            f"First byte (hex): {hex(first_byte) if first_byte is not None else 'N/A'}"
        )

        # Try to decode as text
        try:
            text = response.text
            print(f"\n=== DECODED TEXT ===")
            print(f"Text length: {len(text)} characters")
            print(f"First 500 characters:\n{text[:500]}")

            # Save text response
            with open(f"response_text_{space_id}.txt", "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved text response to response_text_{space_id}.txt")

            # Try to parse JSON
            if text.strip():
                # Check if it starts with ']'
                if text.startswith("]"):
                    print("\nWARNING: Response starts with ']' - looking for JSON...")
                    start = text.find("{")
                    if start != -1:
                        print(f"Found '{{' at position {start}")
                        json_str = text[start:]
                        try:
                            data = json.loads(json_str)
                            print("SUCCESS: Parsed JSON after trimming!")
                            print(f"Response has keys: {list(data.keys())}")

                            # Save parsed JSON
                            with open(f"response_parsed_{space_id}.json", "w") as f:
                                json.dump(data, f, indent=2)
                            print(
                                f"Saved parsed JSON to response_parsed_{space_id}.json"
                            )
                        except json.JSONDecodeError as e:
                            print(f"JSON parse error: {e}")
                            print(
                                f"First 500 chars of trimmed response:\n{json_str[:500]}"
                            )
                    else:
                        print("ERROR: Could not find '{' in response")
                else:
                    # Try to parse as-is
                    try:
                        data = json.loads(text)
                        print("SUCCESS: Parsed JSON directly!")
                        print(f"Response has keys: {list(data.keys())}")
                    except json.JSONDecodeError as e:
                        print(f"JSON parse error: {e}")
                        print("Trying to find JSON in response...")
                        start = text.find("{")
                        if start != -1:
                            print(f"Found '{{' at position {start}")
                            try:
                                data = json.loads(text[start:])
                                print("SUCCESS: Parsed JSON after finding start!")
                            except:
                                print("Still couldn't parse JSON")

        except UnicodeDecodeError as e:
            print(f"\nERROR: Could not decode response as text: {e}")
            print("Response appears to be binary/compressed data")

            # Try to decompress manually
            content_encoding = response.headers.get("content-encoding", "").lower()
            if "br" in content_encoding:
                print("Response is Brotli compressed. Trying to decompress...")
                try:
                    import brotli

                    decompressed = brotli.decompress(response.content)
                    print(
                        f"Decompressed {len(response.content)} bytes to {len(decompressed)} bytes"
                    )
                    text = decompressed.decode("utf-8")
                    print(f"Decoded to text: {len(text)} characters")
                    print(f"First 500 chars:\n{text[:500]}")
                except ImportError:
                    print(
                        "ERROR: brotli module not installed. Install with: pip install brotli"
                    )
                except Exception as e:
                    print(f"ERROR: Brotli decompression failed: {e}")
            elif "gzip" in content_encoding:
                print("Response is gzip compressed. Trying to decompress...")
                import gzip
                import io

                try:
                    decompressed = gzip.decompress(response.content)
                    print(
                        f"Decompressed {len(response.content)} bytes to {len(decompressed)} bytes"
                    )
                    text = decompressed.decode("utf-8")
                    print(f"Decoded to text: {len(text)} characters")
                    print(f"First 500 chars:\n{text[:500]}")
                except Exception as e:
                    print(f"ERROR: Gzip decompression failed: {e}")

    except Exception as e:
        print(f"\nERROR making request: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
