from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.common.config import settings
from backend.desktop.preferences import (
    get_clipboard_collection_enabled,
    get_clipboard_store_raw_text_enabled,
    get_data_collection_enabled,
)


def main() -> int:
    pref_data = get_data_collection_enabled()
    pref_clipboard = get_clipboard_collection_enabled()
    pref_raw = get_clipboard_store_raw_text_enabled()

    resolved_clipboard = pref_data and pref_clipboard
    resolved_raw = resolved_clipboard and pref_raw

    print('Clipboard opt-in runtime verification')
    print(f'settings.CLIPBOARD_COLLECTION_ENABLED = {settings.CLIPBOARD_COLLECTION_ENABLED}')
    print(f'settings.CLIPBOARD_STORE_RAW_TEXT = {settings.CLIPBOARD_STORE_RAW_TEXT}')
    print(f'preference.data_collection = {pref_data}')
    print(f'preference.clipboard_collection = {pref_clipboard}')
    print(f'preference.clipboard_store_raw_text = {pref_raw}')
    print(f'resolved_runtime.clipboard_collection = {resolved_clipboard}')
    print(f'resolved_runtime.clipboard_store_raw_text = {resolved_raw}')
    print()
    print('Expected fixed behavior: TelemetryManager synchronizes runtime flags to these resolved values on start/save.')

    if pref_clipboard and not resolved_clipboard:
        print('FAIL: clipboard opt-in is masked because telemetry data collection is disabled.')
        return 1

    print('PASS: runtime resolution for clipboard capture is internally consistent.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
