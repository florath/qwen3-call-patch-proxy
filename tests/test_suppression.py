#!/usr/bin/env python3
"""
Test that empty named tool calls are suppressed
"""
import sys
import os
import json
import asyncio
sys.path.insert(0, os.path.dirname(__file__))

from call_patch_proxy import (
    RequestState, 
    process_sse_event
)

async def test_empty_named_call_suppression():
    """Test that empty named tool calls are suppressed"""
    print("Testing empty named tool call suppression:")
    
    # Create request state
    request_id = "test-suppression"
    request_state = RequestState(request_id=request_id)
    
    # Mock request_states
    from call_patch_proxy import request_states
    request_states[request_id] = request_state
    
    try:
        # Test 1: SSE event with ONLY empty named tool call (should be suppressed)
        event1 = {
            "choices": [{
                "delta": {
                    "tool_calls": [{
                        "id": "call_12345",
                        "function": {
                            "name": "todowrite",
                            "arguments": ""
                        }
                    }]
                }
            }]
        }
        
        print("  Testing empty named tool call:")
        fixed_event1 = await process_sse_event(event1, request_id)
        
        # Check if tool_calls was removed or empty
        delta1 = fixed_event1["choices"][0]["delta"]
        if "tool_calls" not in delta1 or len(delta1["tool_calls"]) == 0:
            print("  ✓ Empty named tool call suppressed")
        else:
            print("  ✗ Empty named tool call not suppressed")
            return False
        
        # Test 2: Mixed event with empty named call AND fragments
        event2 = {
            "choices": [{
                "delta": {
                    "tool_calls": [
                        {
                            "id": "call_67890", 
                            "function": {
                                "name": "todowrite",
                                "arguments": ""
                            }
                        },
                        {"index": 1, "function": {"arguments": "{"}},
                        {"index": 2, "function": {"arguments": '"todos": "[]"'}},
                        {"index": 3, "function": {"arguments": "}"}}
                    ]
                }
            }]
        }
        
        print("  Testing mixed empty named + fragments:")
        fixed_event2 = await process_sse_event(event2, request_id)
        
        # Check the result
        delta2 = fixed_event2["choices"][0]["delta"]
        if "tool_calls" in delta2 and len(delta2["tool_calls"]) == 1:
            tool_call = delta2["tool_calls"][0] 
            if "index" in tool_call and tool_call.get("function", {}).get("name") == "todowrite":
                print("  ✓ Empty named call suppressed, fragments consolidated")
            else:
                print("  ✗ Result not as expected")
                print(f"    Tool call: {tool_call}")
                return False
        else:
            print("  ✗ Expected 1 tool call after processing")
            print(f"    Got: {delta2.get('tool_calls', [])}")
            return False
            
        return True
        
    finally:
        # Cleanup
        if request_id in request_states:
            del request_states[request_id]

async def main():
    print("Testing tool call suppression logic...\n")
    
    success = await test_empty_named_call_suppression()
    
    if success:
        print("\n🎉 Tool call suppression test passed!")
        return 0
    else:
        print("\n❌ Tool call suppression test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))