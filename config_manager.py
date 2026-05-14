#!/usr/bin/env python3
"""
GitHub Gist Config Manager
Reads/writes events.yaml from private Gist for persistence
"""
import os
import requests
import yaml
from typing import Dict, List, Optional

class ConfigManager:
    """Manage events config via GitHub Gist"""

    def __init__(self):
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.gist_id = os.environ.get('GIST_ID')

        if not self.github_token or not self.gist_id:
            raise ValueError("GITHUB_TOKEN and GIST_ID environment variables required")

    def _gist_url(self) -> str:
        return f"https://api.github.com/gists/{self.gist_id}"

    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def read_config(self) -> Dict:
        """Read events.yaml from Gist"""
        try:
            response = requests.get(self._gist_url(), headers=self._headers(), timeout=10)
            response.raise_for_status()

            gist_data = response.json()
            yaml_content = gist_data['files']['events.yaml']['content']

            config = yaml.safe_load(yaml_content)
            return config if config else {'events': []}

        except Exception as e:
            print(f"⚠️ Error reading Gist: {e}")
            return {'events': []}

    def write_config(self, config: Dict) -> bool:
        """Write events.yaml to Gist"""
        try:
            yaml_content = yaml.dump(config, default_flow_style=False, allow_unicode=True)

            payload = {
                'files': {
                    'events.yaml': {
                        'content': yaml_content
                    }
                }
            }

            response = requests.patch(
                self._gist_url(),
                headers=self._headers(),
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            print("✅ Config saved to Gist")
            return True

        except Exception as e:
            print(f"⚠️ Error writing Gist: {e}")
            return False

    def get_events(self) -> List[Dict]:
        """Get all enabled events"""
        config = self.read_config()
        return [e for e in config.get('events', []) if e.get('enabled', True)]

    def add_event(self, event_id: str, name: str, url: str, tickets: List[str]) -> bool:
        """Add new event to config"""
        config = self.read_config()

        # Check if event ID already exists
        if any(e['id'] == event_id for e in config.get('events', [])):
            print(f"⚠️ Event {event_id} already exists")
            return False

        new_event = {
            'id': event_id,
            'name': name,
            'url': url,
            'tickets': tickets,
            'enabled': True
        }

        if 'events' not in config:
            config['events'] = []

        config['events'].append(new_event)
        return self.write_config(config)

    def remove_event(self, event_id: str) -> bool:
        """Remove event from config"""
        config = self.read_config()

        events = config.get('events', [])
        original_count = len(events)

        config['events'] = [e for e in events if e['id'] != event_id]

        if len(config['events']) == original_count:
            print(f"⚠️ Event {event_id} not found")
            return False

        return self.write_config(config)

    def toggle_event(self, event_id: str, enabled: bool) -> bool:
        """Enable/disable event"""
        config = self.read_config()

        for event in config.get('events', []):
            if event['id'] == event_id:
                event['enabled'] = enabled
                return self.write_config(config)

        print(f"⚠️ Event {event_id} not found")
        return False


# Convenience function for scripts
def get_config_manager() -> Optional[ConfigManager]:
    """Get ConfigManager instance or None if not configured"""
    try:
        return ConfigManager()
    except ValueError as e:
        print(f"⚠️ Config not available: {e}")
        return None
