#!/usr/bin/env python3
import json
import sys
import time

def main():
    input_data = json.loads(sys.stdin.read())
    processed_data = input_data.get('processed_data', {})
    validation_result = input_data.get('validation_result', {})
    
    time.sleep(2)
    
    final_result = {
        'summary': f"Processed {processed_data.get('record_count', 0)} records successfully",
        'original_text': processed_data.get('original_text', ''),
        'processed_text': processed_data.get('processed_text', ''),
        'validation_status': validation_result.get('validation_message', ''),
        'transformations': processed_data.get('transformations_applied', []),
        'processing_complete': True,
        'final_status': 'success'
    }
    
    result = {
        'success': True,
        'outputs': {
            'final_result': final_result,
            'status': 'completed'
        }
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
