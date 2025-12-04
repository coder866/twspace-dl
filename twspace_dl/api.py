from __future__ import annotations

import json
import logging
import re
from typing import Any, NoReturn

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import ConnectionError, HTTPError, JSONDecodeError, RetryError

from .cookies import validate_cookies

"""Twitter unofficial API authorization header."""
TWITTER_AUTHORIZATION = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

"""Retry parameters for making all requests."""
RETRY = Retry(
    total=5,
    connect=3,
    read=2,
    redirect=3,
    backoff_factor=0.2,
    status_forcelist=(500, 502, 503, 504),
)

"""Default connection timeout for making all requests."""
TIMEOUT = 20


class HTTPClient:
    """The HTTP client for making requests."""

    def __init__(self) -> None:
        """Initialize the client with a requests session and mount the default retry adapter."""
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=RETRY))

    def get(
        self,
        url: str,
        params: dict[str, str] = {},
        headers: dict[str, str] = {},
        cookies: dict[str, str] = {},
        timeout: int = TIMEOUT,
    ) -> requests.Response:
        """Send HTTP GET requests to the specified URL.

        - url: The URL to send the GET request to.
        - params: Query parameters of the request.
        - headers: HTTP headers of the request.
        - cookies: HTTP cookies of the request.
        - timeout: The connection timeout of the request, default to the static value specified above.

        - return: The response of the request.

        - raise RuntimeError: Raised when the request was not successful (max retries, timeouts, and
        4xx and 5xx HTTP status codes).
        """
        try:
            logging.debug(f"HTTP GET: {url}")
            logging.debug(f"Params: {params}")

            # Make the request
            response = self.session.get(
                url, params=params, headers=headers, cookies=cookies, timeout=timeout
            )

            # Log response info for debugging
            logging.debug(f"Response status: {response.status_code}")
            logging.debug(f"Response URL: {response.url}")
            logging.debug(f"Response encoding: {response.encoding}")
            logging.debug(f"Response apparent encoding: {response.apparent_encoding}")

            # Try to fix encoding if needed
            if response.encoding is None:
                response.encoding = "utf-8"

            # Check the raw content first few bytes
            logging.debug(f"First 100 bytes of raw content: {response.content[:100]}")

            response.raise_for_status()
            return response
        except RetryError as e:
            logging.error(
                f"Max retries exceeded with URL: {e.request.url}, reason: {e.args[0].reason}"
            )
            raise RuntimeError("API request failed after max retries") from e
        except ConnectionError as e:
            logging.error(
                f"Connection error occurred with URL: {e.request.url}, reason: {e.args[0].reason}"
            )
            raise RuntimeError("API request failed with connection error") from e
        except HTTPError as e:
            if e.response.status_code == 404:
                logging.error(f"API endpoint not found (404): {url}")
                logging.debug(f"Response headers: {dict(e.response.headers)}")
                logging.debug(f"Response text: {e.response.text[:2000]}")
                raise RuntimeError(
                    f"Twitter API endpoint not found. Status: {e.response.status_code}"
                ) from e
            elif e.response.status_code == requests.codes.TOO_MANY_REQUESTS:
                logging.error(f"API rate limit exceeded with URL: {url}")
                raise RuntimeError("API rate limit exceeded") from e
            elif e.response.status_code == 403:
                logging.error(f"Access forbidden (403) for URL: {url}")
                logging.debug(f"Response text: {e.response.text[:2000]}")
                raise RuntimeError(
                    "Access forbidden. Check your cookies/authentication."
                ) from e
            logging.error(
                f"HTTP error occurred with URL: {e.request.url}, status code: {e.response.status_code}"
            )
            logging.debug(f"Response text: {e.response.text[:2000]}")
            raise RuntimeError(
                f"API request failed with HTTP error: {e.response.status_code}"
            ) from e

    # def get(
    #     self,
    #     url: str,
    #     params: dict[str, str] = {},
    #     headers: dict[str, str] = {},
    #     cookies: dict[str, str] = {},
    #     timeout: int = TIMEOUT,
    # ) -> requests.Response:
    #     """Send HTTP GET requests to the specified URL.

    #     - url: The URL to send the GET request to.
    #     - params: Query parameters of the request.
    #     - headers: HTTP headers of the request.
    #     - cookies: HTTP cookies of the request.
    #     - timeout: The connection timeout of the request, default to the static value specified above.

    #     - return: The response of the request.

    #     - raise RuntimeError: Raised when the request was not successful (max retries, timeouts, and
    #     4xx and 5xx HTTP status codes).
    #     """
    #     try:
    #         logging.debug(f"HTTP GET: {url}")
    #         logging.debug(f"Params: {params}")
    #         logging.debug(f"Headers keys: {list(headers.keys())}")

    #         response = self.session.get(
    #             url, params=params, headers=headers, cookies=cookies, timeout=timeout
    #         )

    #         # Log response info for debugging
    #         logging.debug(f"Response status: {response.status_code}")
    #         logging.debug(f"Response URL: {response.url}")
    #         if response.status_code != 200:
    #             logging.debug(f"Response text (first 1000 chars): {response.text[:1000]}")

    #         response.raise_for_status()
    #         return response
    #     except RetryError as e:
    #         logging.error(
    #             f"Max retries exceeded with URL: {e.request.url}, reason: {e.args[0].reason}"
    #         )
    #         raise RuntimeError("API request failed after max retries") from e
    #     except ConnectionError as e:
    #         logging.error(
    #             f"Connection error occurred with URL: {e.request.url}, reason: {e.args[0].reason}"
    #         )
    #         raise RuntimeError("API request failed with connection error") from e
    #     except HTTPError as e:
    #         if e.response.status_code == 404:
    #             logging.error(f"API endpoint not found (404): {url}")
    #             logging.debug(f"Response headers: {dict(e.response.headers)}")
    #             logging.debug(f"Response text: {e.response.text[:2000]}")
    #             raise RuntimeError(f"Twitter API endpoint not found. The API might have changed. Status: {e.response.status_code}") from e
    #         elif e.response.status_code == requests.codes.TOO_MANY_REQUESTS:
    #             logging.error(f"API rate limit exceeded with URL: {url}")
    #             raise RuntimeError("API rate limit exceeded") from e
    #         elif e.response.status_code == 403:
    #             logging.error(f"Access forbidden (403) for URL: {url}")
    #             logging.debug(f"Response text: {e.response.text[:2000]}")
    #             raise RuntimeError("Access forbidden. Check your cookies/authentication.") from e
    #         logging.error(
    #             f"HTTP error occurred with URL: {e.request.url}, status code: {e.response.status_code}"
    #         )
    #         logging.debug(f"Response text: {e.response.text[:2000]}")
    #         raise RuntimeError(f"API request failed with HTTP error: {e.response.status_code}") from e

    # def get(
    #     self,
    #     url: str,
    #     params: dict[str, str] = {},
    #     headers: dict[str, str] = {},
    #     cookies: dict[str, str] = {},
    #     timeout: int = TIMEOUT,
    # ) -> requests.Response:
    #     """Send HTTP GET requests to the specified URL.

    #     - url: The URL to send the GET request to.
    #     - params: Query parameters of the request.
    #     - headers: HTTP headers of the request.
    #     - cookies: HTTP cookies of the request.
    #     - timeout: The connection timeout of the request, default to the static value specified above.

    #     - return: The response of the request.

    #     - raise RuntimeError: Raised when the request was not successful (max retries, timeouts, and
    #       4xx and 5xx HTTP status codes).
    #     """
    #     try:
    #         response = self.session.get(
    #             url, params=params, headers=headers, cookies=cookies, timeout=timeout
    #         )
    #         response.raise_for_status()
    #         return response
    #     except RetryError as e:
    #         logging.error(
    #             f"Max retries exceeded with URL: {e.request.url}, reason: {e.args[0].reason}"
    #         )
    #         raise RuntimeError("API request failed after max retries") from e
    #     except ConnectionError as e:
    #         logging.error(
    #             f"Connection error occurred with URL: {e.request.url}, reason: {e.args[0].reason}"
    #         )
    #         raise RuntimeError("API request failed with connection error") from e
    #     except HTTPError as e:
    #         if e.response.status_code == requests.codes.TOO_MANY_REQUESTS:
    #             logging.error(f"API rate limit exceeded with URL: {url}")
    #             raise
    #         logging.error(
    #             f"HTTP error occurred with URL: {e.request.url}, status code: {e.response.status_code}"
    #         )
    #         raise RuntimeError("API request failed with HTTP error") from e


class APIClient:
    """Base API client."""

    """Base URL of the API."""
    _API_URL = "https://x.com/i/api"

    def __init__(self, client: HTTPClient, path: str, cookies: dict[str, str]) -> None:
        """Initialize the API client.

        - client: The `HTTPClient` instance to send requests.
        - path: The path to add to the base URL of the API.
        - cookies: The cookies used for making all requests to the API.
        """
        validate_cookies(cookies)
        self.client = client
        self.base_url = self.join_url(self._API_URL, path)
        self.cookies = cookies

        # Get the ct0 token from cookies
        ct0_token = cookies.get("ct0", "")

        # Use the EXACT headers that worked in the test script
        self.headers = {
            "authorization": TWITTER_AUTHORIZATION,
            "x-csrf-token": ct0_token,
            "content-type": "application/json",
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "accept": "*/*",
            # CRITICAL: Use gzip, deflate ONLY (no brotli)
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

    def join_url(self, *paths: str) -> str:
        """Join all the specified paths to a single URL.

        - paths: The components of the URL to be joined.
        """
        return "/".join(path.strip("/") for path in paths)

    def get(self, path: str, params: dict[str, str] = {}) -> Any:
        """Send HTTP GET requests to the specified path of the API with the specified query parameters.

        - path: The path to send the API request to.
        - params: Query parameters of the request.

        - return: The object decoded from the JSON string returned from the API.

        - raise RuntimeError: If the response from the API cannot be decoded as a JSON string.
        """
        try:
            # Build the full URL
            full_url = self.join_url(self.base_url, path)

            # Log the request for debugging
            logging.debug(f"Making API request to: {full_url}")
            logging.debug(f"Params: {params}")
            logging.debug(f"Headers being sent: {self.headers}")

            # Use self.client.get() instead of trying to access session directly
            response = self.client.get(
                full_url,
                params=params,
                headers=self.headers,
                cookies=self.cookies,
            )

            # Debug: Log response status
            logging.debug(f"Response status: {response.status_code}")
            logging.debug(f"Response URL: {response.url}")
            logging.debug(
                f"Content-Encoding: {response.headers.get('content-encoding')}"
            )
            logging.debug(f"Content-Length: {len(response.content)}")

            # Check first character of response
            if response.text:
                first_char = response.text[0] if response.text else "None"
                logging.debug(
                    f"First character of response: '{first_char}' (ord: {ord(first_char) if first_char != 'None' else 'N/A'})"
                )

            return response.json()

        except JSONDecodeError:
            logging.error(
                f"Cannot decode response from URL: {response.url}, status code: {response.status_code}"
            )
            logging.error(f"Response headers: {dict(response.headers)}")
            logging.error(f"Response text (first 500 chars): {response.text[:500]}")
            # Check what the actual content is
            logging.error(
                f"Raw content (first 20 bytes hex): {response.content[:20].hex()}"
            )
            raise RuntimeError("API response cannot be decoded as JSON")

    # def get(self, path: str, params: dict[str, str] = {}) -> Any:
    #     """Send HTTP GET requests to the specified path of the API with the specified query parameters.

    #     - path: The path to send the API request to.
    #     - params: Query parameters of the request.

    #     - return: The object decoded from the JSON string returned from the API.

    #     - raise RuntimeError: If the response from the API cannot be decoded as a JSON string.
    #     """
    #     try:
    #         # Build the full URL
    #         full_url = self.join_url(self.base_url, path)

    #         # Log the request for debugging
    #         logging.debug(f"Making API request to: {full_url}")
    #         logging.debug(f"Params: {params}")

    #         # Use self.client.get() instead of trying to access session directly
    #         response = self.client.get(
    #             full_url,
    #             params=params,
    #             headers=self.headers,
    #             cookies=self.cookies,
    #         )
    #         return response.json()
    #     except JSONDecodeError:
    #         logging.error(
    #             f"Cannot decode response from URL: {response.url}, status code: {response.status_code}"
    #         )
    #         logging.debug(f"Response text: {response.text!r}")
    #         raise RuntimeError("API response cannot be decoded as JSON")


class GraphQLAPI(APIClient):
    """Twitter GraphQL API client."""

    def __init__(self, client: HTTPClient, path: str, cookies: dict[str, str]) -> None:
        """Initialize the Twitter GraphQL API client.

        - client: The `HTTPClient` instance to send requests.
        - path: The path to add to the base URL of the API.
        - cookies: The cookies used for making all requests to the API.
        """
        # Ensure we're using the correct path for GraphQL API
        super().__init__(client, "graphql", cookies)

    def get(
        self,
        query_id: str,
        operation_name: str,
        variables: dict[str, str] | str,
        features: dict[str, str] | str | None = None,
    ) -> Any:
        """Send HTTP GET requests to the Twitter GraphQL API.

        - query_id: The query ID of the GraphQL API endpoint.
        - operation_name: The name of the operation to be executed.
        - variables: Query variables of the GraphQL query.
        - features: Feature switches of the GraphQL query.

        - return: The returned object of the query.
        """
        # Convert variables to JSON string if it's a dict
        if isinstance(variables, dict):
            variables_str = json.dumps(variables, separators=(",", ":"))
        else:
            variables_str = variables

        params = {
            "variables": variables_str,
        }

        if features:
            if isinstance(features, dict):
                features_str = json.dumps(features, separators=(",", ":"))
            else:
                features_str = features
            params["features"] = features_str

        # Build the endpoint path
        endpoint_path = f"{query_id}/{operation_name}"

        # Log the request for debugging
        logging.debug(f"Making GraphQL request to: {endpoint_path}")
        logging.debug(f"Query ID: {query_id}")
        logging.debug(f"Operation: {operation_name}")
        logging.debug(
            f"Variables: {variables_str[:100]}..."
            if len(variables_str) > 100
            else f"Variables: {variables_str}"
        )

        # Fix: Check if features is a string before slicing
        if features:
            if isinstance(features, str):
                logging.debug(
                    f"Features: {features[:100]}..."
                    if len(features) > 100
                    else f"Features: {features}"
                )
            else:
                logging.debug(f"Features (type: {type(features)}): {features}")

        return super().get(endpoint_path, params)

    def _dump_json(self, obj: Any) -> str:
        """Serialize the object to a compact JSON string.

        The object will be returned directly if it is a string.

        - obj: The object to be serialized to JSON.

        - return: A compact JSON string representing the specified object.
        """
        if isinstance(obj, str):
            return obj
        return json.dumps(obj, indent=None, separators=(",", ":"))

    # def audio_space_by_id(self, space_id: str) -> dict:
    #     """Query Twitter Space details by its ID.

    #     - space_id: The ID of the Twitter Space.

    #     - return: The details of the queried Twitter Space.
    #     """
    #     # Valid ID as of Dec 2025
    #     query_id = "rC2zlE1t7SHbVG8obPZliQ"
    #     operation_name = "AudioSpaceById"

    #     variables = {
    #         "id": space_id,
    #         "isMetatagsQuery": False,  # UPDATED: Changed from True to False
    #         "withReplays": True,
    #         "withListeners": True,
    #     }

    #     # UPDATED: Exact features map from your browser inspection
    #     features = (
    #         '{"spaces_2022_h2_spaces_communities":true,"spaces_2022_h2_clipping":true,'
    #         '"creator_subscriptions_tweet_preview_api_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,'
    #         '"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,'
    #         '"verified_phone_label_enabled":false,"premium_content_api_read_enabled":false,'
    #         '"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,'
    #         '"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,'
    #         '"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,'
    #         '"articles_preview_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,'
    #         '"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,'
    #         '"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,'
    #         '"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,'
    #         '"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,'
    #         '"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,'
    #         '"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,'
    #         '"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,'
    #         '"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,'
    #         '"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,'
    #         '"responsive_web_enhance_cards_enabled":false}'
    #     )

    #     return self.get(query_id, operation_name, variables, features)

    # def audio_space_by_id(self, space_id: str) -> dict:
    #     """Query Twitter Space details by its ID.

    #     - space_id: The ID of the Twitter Space.

    #     - return: The details of the queried Twitter Space.
    #     """
    #     # Valid ID as of Dec 2025
    #     query_id = "rC2zlE1t7SHbVG8obPZliQ"
    #     operation_name = "AudioSpaceById"

    #     variables = {
    #         "id": space_id,
    #         "isMetatagsQuery": False,
    #         "withReplays": True,
    #         "withListeners": True,
    #     }

    #     # Use the exact features string from browser request
    #     features = '{"spaces_2022_h2_spaces_communities":true,"spaces_2022_h2_clipping":true,"creator_subscriptions_tweet_preview_api_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}'

    #     return self.get(query_id, operation_name, variables, features)

    def audio_space_by_id(self, space_id: str) -> dict:
        """Query Twitter Space details by its ID.

        - space_id: The ID of the Twitter Space.

        - return: The details of the queried Twitter Space.
        """
        # Valid ID as of Dec 2025
        query_id = "rC2zlE1t7SHbVG8obPZliQ"
        operation_name = "AudioSpaceById"

        variables = {
            "id": space_id,
            "isMetatagsQuery": False,
            "withReplays": True,
            "withListeners": True,
        }

        # Use the EXACT features string from your successful test
        features = '{"spaces_2022_h2_spaces_communities":true,"spaces_2022_h2_clipping":true,"creator_subscriptions_tweet_preview_api_enabled":true,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}'

        return self.get(query_id, operation_name, variables, features)

    def audio_space_by_id_fixed(self, space_id: str) -> dict:
        """Alternative method to handle malformed JSON responses."""
        import json
        from urllib.parse import urlencode

        # Build the exact URL
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

        # URL encode the parameters
        encoded_vars = urlencode(
            {"variables": json.dumps(variables, separators=(",", ":"))}
        )
        encoded_features = urlencode({"features": features})

        url = f"https://x.com/i/api/graphql/rC2zlE1t7SHbVG8obPZliQ/AudioSpaceById?{encoded_vars}&{encoded_features}"

        logging.debug(f"Making direct request to: {url}")

        # FIX: Use self.client.get() instead of self.client.session.get()
        response = self.client.get(url, headers=self.headers, cookies=self.cookies)

        # Handle the malformed JSON response
        text = response.text

        # If response starts with ']', find the actual JSON
        if text.startswith("]"):
            start_idx = text.find("{")
            if start_idx != -1:
                text = text[start_idx:]
                logging.debug(f"Trimmed {start_idx} characters before '{{'")

        # Try to parse the JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON even after cleaning: {e}")
            logging.error(f"Cleaned text (first 500 chars): {text[:500]}")
            raise RuntimeError("Could not decode API response as JSON")

    def user_by_screen_name(self, screen_name: str) -> dict:
        """Query Twitter user details by their screen name (@ handle).

        - screen_name: The screen name (@ handle) of the Twitter user.

        - return: The details of the queried Twitter user.
        """
        # Updated query_id based on common Twitter API patterns
        query_id = "G3KGOASz96M-Qu0nwmGXNg"
        operation_name = "UserByScreenName"
        variables = {"screen_name": screen_name, "withSafetyModeUserFields": True}

        # Updated features string to match current Twitter requirements
        features = '{"hidden_profile_likes_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"tweetypie_unmention_optimization_enabled":true,"vibe_api_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"rweb_video_timestamps_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}'

        return self.get(query_id, operation_name, variables, features)

    # In api.py, update the profile_spotlights_query method:

    def profile_spotlights_query(self, screen_name: str) -> dict:
        """Backup API endpoint to query Twitter user details by their screen name (@ handle).

        The response data from this API contains less information of the user than the `user_by_screen_name`
        API, but still has the essential `rest_id` field. Therefore, it is used as a backup of the other API
        endpoint if the other one was rate limited.

        - screen_name: The screen name (@ handle) of the Twitter user.

        - return: The details of the queried Twitter user.
        """
        # Updated query_id
        query_id = "9zwVLJ48lmVUk8u_Gh9DmA"
        operation_name = "ProfileSpotlightsQuery"
        variables = {"screen_name": screen_name}

        # Add features parameter
        features = '{"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_enhance_cards_enabled":false}'

        return self.get(query_id, operation_name, variables, features)

    def user_id(self, screen_name: str) -> str:
        """Retrieve the numeric user ID (`rest_id`) of the user with the specified screen name (@ handle).

        - screen_name: The screen name (@ handle) of the Twitter user.

        - return: The numeric user ID (`rest_id`) of the specified user.
        """
        try:
            data = self.user_by_screen_name(screen_name)
            return data["data"]["user"]["result"]["rest_id"]
        except HTTPError:
            logging.warning("Trying with backup endpoint")
            data = self.profile_spotlights_query(screen_name)
            return data["data"]["user_result_by_screen_name"]["result"]["rest_id"]

    def user_id_from_url(self, user_url: str) -> str:
        """Retrieve the numeric user ID (`rest_id`) of the user that the specified profile URL linked to.

        Supported URL formats:
        - https://x.com/<screen_name>
        - http://x.com/<screen_name>
        - x.com/<screen_name>
        and with any number of trailing slashes (`/`).

        - user_url: The URL pointing to the profile of the Twitter user.

        - return: The numeric user ID (`rest_id`) of the specified user.

        - raise RuntimeError: If the specified URL is not a valid Twitter user profile URL.
        """
        if match := re.match(
            r"^(?:https?:\/\/|)x\.com\/(?P<screen_name>\w+)$", user_url.strip("/")
        ):
            return self.user_id(match.group("screen_name"))
        raise RuntimeError(f"Invalid Twitter user URL: {user_url}")


class FleetsAPI(APIClient):
    """Twitter Fleets API client."""

    def __init__(self, client: HTTPClient, path: str, cookies: dict[str, str]) -> None:
        """Initialize the Twitter Fleets API client.

        - client: The `HTTPClient` instance to send requests.
        - path: The path to add to the base URL of the API.
        - cookies: The cookies used for making all requests to the API.
        """
        super().__init__(client, path, cookies)

    def get(self, version: str, endpoint: str, params: dict[str, str]) -> Any:
        """Send HTTP GET requests to the Twitter Fleets API.

        - version: The version of the API.
        - endpoint: The endpoint of the API.
        - params: Query parameters of the request.

        - return: The object returned in the response of the API.
        """
        return super().get(self.join_url(version, endpoint), params)

    def avatar_content(self, *user_ids: str) -> dict:
        """Retrieve Twitter Space details of the specified user IDs.

        This endpoint limits to a maximum of 100 user IDs per request.

        - user_ids: Numeric user IDs (`rest_id`) of users.

        - return: Twitter Space details of the specified user IDs. Only ongoing Twitter Spaces will be returned.
        """
        if len(user_ids) > 100:
            raise RuntimeError(
                "Number of user IDs exceeded the limit of 100 per request"
            )
        version = "v1"
        endpoint = "avatar_content"
        params = {"user_ids": ",".join(user_ids), "only_spaces": "true"}
        return self.get(version, endpoint, params)


class LiveVideoStreamAPI(APIClient):
    """Twitter Live Video Stream API client."""

    def __init__(self, client: HTTPClient, path: str, cookies: dict[str, str]) -> None:
        """Initialize the Twitter Live Video Stream API client.

        - client: The `HTTPClient` instance to send requests.
        - path: The path to add to the base URL of the API.
        - cookies: The cookies used for making all requests to the API.
        """
        super().__init__(client, path, cookies)

    def status(self, media_key: str) -> dict:
        """Retrieve Twitter Space media playlist details by the specified media key.

        - media_key: The media key of the Twitter Space.

        - return: The media playlist details of the specified media key.
        """
        return super().get(self.join_url("status", media_key))


class DummyAPI:
    """Dummy API class used for uninitialized APIs."""

    def __init__(self, api_name: str = "API") -> None:
        self.api_name = api_name

    def __getattr__(self, name: str) -> NoReturn:
        """Show a clear message to the user if the API was not initialized.

        - raise RuntimeError: If any attribute of the class is accessed or any method is called.
        """
        raise RuntimeError(f"{self.api_name} is not initialized")

    def __bool__(self) -> False:
        """Always evaluate instances of the class to `False`.

        This is just for the convenience of testing the instance directly in `if` statements:
        >>> api = DummyAPI()
        ... if api:  # non-dummy API instances would evaluate to `True`
        ...     # do something if the API was initialized
        ...     pass
        See also: `TwitterAPI.__bool__()`

        - return: `False`.
        """
        return False


class TwitterAPI:
    """The collection of all Twitter APIs."""

    def __init__(self) -> None:
        """Initialize the instance of the Twitter API collection.

        Note that this will not initialize APIs in this collection. They will initially only be an
        instance of the `DummyAPI` class.
        They need to be initialized by calling the `init_apis()` method with cookies of the user.
        """
        self.client = HTTPClient()
        self.graphql_api = DummyAPI("Twitter GraphQL API")
        self.fleets_api = DummyAPI("Twitter Fleets API")
        self.live_video_stream_api = DummyAPI("Twitter Live Video Stream API")

    def init_apis(self, cookies: dict[str, str]) -> None:
        """Initialize all APIs in this collection with the specified cookies."""
        self.graphql_api = GraphQLAPI(self.client, "graphql", cookies)
        self.fleets_api = FleetsAPI(self.client, "fleets", cookies)
        self.live_video_stream_api = LiveVideoStreamAPI(
            self.client, "1.1/live_video_stream", cookies
        )

    def __bool__(self) -> bool:
        """Determine if all APIs are initialized.

        This is just for the convenience of testing the instance directly in `if` statements:
        >>> api = TwitterAPI()
        ... if api:
        ...     print("API initialized")  # would run if all APIs in the `api` instance are initialized
        See also: `DummyAPI.__bool__()`

        - return: `True` if and only if all APIs are initialized, `False` otherwise.
        """
        return bool(self.graphql_api and self.fleets_api and self.live_video_stream_api)


"""The global instance of the collection of Twitter APIs."""
API = TwitterAPI()
