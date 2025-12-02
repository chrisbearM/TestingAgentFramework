"""
Test script to verify C8 token validation is working correctly.
Tests token estimation, validation, and truncation functionality.
"""
import sys
import io

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.ai_tester.utils.token_manager import (
    estimate_tokens,
    check_token_limit,
    validate_prompt_size,
    truncate_to_token_limit,
    get_max_tokens_for_model
)


def test_token_estimation():
    """Test C8: Token estimation accuracy"""
    print("\n" + "="*80)
    print("Testing C8: Token Estimation")
    print("="*80)

    test_cases = [
        ("Hello world", 2, 5),  # Simple text: 2-5 tokens
        ("A" * 100, 20, 30),    # 100 chars: ~20-30 tokens
        ("A" * 1000, 200, 300), # 1000 chars: ~200-300 tokens
    ]

    passed = 0
    failed = 0

    for text, min_expected, max_expected in test_cases:
        token_count = estimate_tokens(text, model="gpt-4o")
        if min_expected <= token_count <= max_expected:
            print(f"✅ PASS: '{text[:20]}...' -> {token_count} tokens (expected {min_expected}-{max_expected})")
            passed += 1
        else:
            print(f"❌ FAIL: '{text[:20]}...' -> {token_count} tokens (expected {min_expected}-{max_expected})")
            failed += 1

    print(f"\n📊 Token Estimation Results: {passed} passed, {failed} failed")
    return failed == 0


def test_token_limit_validation():
    """Test C8: Token limit validation"""
    print("\n" + "="*80)
    print("Testing C8: Token Limit Validation")
    print("="*80)

    model = "gpt-4o"
    max_tokens = get_max_tokens_for_model(model)
    print(f"Model: {model}, Max tokens: {max_tokens}")

    # Test case 1: Text that fits
    short_text = "This is a short text that should fit easily."
    fits, current, max_allowed = check_token_limit(short_text, model=model)
    if fits:
        print(f"✅ PASS: Short text ({current} tokens) fits within limit ({max_allowed} tokens)")
    else:
        print(f"❌ FAIL: Short text should fit but doesn't")
        return False

    # Test case 2: Text that exceeds limit
    # Create text with ~130k tokens (exceeds 128k limit)
    long_text = "A" * 500000  # ~125k tokens
    fits, current, max_allowed = check_token_limit(long_text, model=model, response_reserve=4000)
    if not fits:
        print(f"✅ PASS: Long text ({current} tokens) correctly identified as exceeding limit ({max_allowed} tokens)")
    else:
        print(f"❌ FAIL: Long text should exceed limit but doesn't")
        return False

    print(f"\n📊 Token Limit Validation: All tests passed")
    return True


def test_prompt_size_validation():
    """Test C8: Prompt size validation for system + user prompts"""
    print("\n" + "="*80)
    print("Testing C8: Prompt Size Validation")
    print("="*80)

    model = "gpt-4o"

    # Test case 1: Normal prompts that fit
    system_prompt = "You are a helpful assistant."
    user_prompt = "What is the capital of France?"

    validation = validate_prompt_size(system_prompt, user_prompt, model=model)

    if validation["valid"]:
        print(f"✅ PASS: Normal prompts fit within limit")
        print(f"  System tokens: {validation['system_tokens']}")
        print(f"  User tokens: {validation['user_tokens']}")
        print(f"  Total tokens: {validation['total_tokens']}")
        print(f"  Max allowed: {validation['max_allowed']}")
    else:
        print(f"❌ FAIL: Normal prompts should fit")
        return False

    # Test case 2: Very large user prompt
    large_user_prompt = "A" * 500000  # ~125k tokens

    validation = validate_prompt_size(system_prompt, large_user_prompt, model=model)

    if not validation["valid"]:
        print(f"✅ PASS: Large prompt correctly identified as exceeding limit")
        print(f"  Total tokens: {validation['total_tokens']}")
        print(f"  Max allowed: {validation['max_allowed']}")
        print(f"  Exceeds by: {validation['exceeds_by']}")
    else:
        print(f"❌ FAIL: Large prompt should exceed limit")
        return False

    print(f"\n📊 Prompt Size Validation: All tests passed")
    return True


def test_truncation():
    """Test C8: Smart text truncation"""
    print("\n" + "="*80)
    print("Testing C8: Smart Text Truncation")
    print("="*80)

    # Create text with sentences
    text = """This is the first sentence. This is the second sentence. This is the third sentence.
This is the fourth sentence. This is the fifth sentence. This is the sixth sentence."""

    # Truncate to 50 tokens
    truncated = truncate_to_token_limit(
        text,
        max_tokens=50,
        model="gpt-4o",
        truncation_strategy="end",
        preserve_structure=True
    )

    truncated_tokens = estimate_tokens(truncated, model="gpt-4o")

    if truncated_tokens <= 50:
        print(f"✅ PASS: Truncation successful")
        print(f"  Original: {estimate_tokens(text, model='gpt-4o')} tokens")
        print(f"  Truncated: {truncated_tokens} tokens (limit: 50)")
        print(f"  Preserved structure: {truncated.endswith('.')}")
    else:
        print(f"❌ FAIL: Truncation did not reduce tokens sufficiently")
        return False

    # Test that original text is returned if within limit
    short_text = "Short text."
    truncated_short = truncate_to_token_limit(short_text, max_tokens=100, model="gpt-4o")

    if truncated_short == short_text:
        print(f"✅ PASS: Short text returned unchanged")
    else:
        print(f"❌ FAIL: Short text should not be modified")
        return False

    print(f"\n📊 Truncation: All tests passed")
    return True


def main():
    """Run all C8 token validation tests"""
    print("\n" + "="*80)
    print("C8 TOKEN VALIDATION TEST SUITE")
    print("="*80)

    results = []

    # Test 1: Token Estimation
    try:
        estimation_pass = test_token_estimation()
        results.append(("Token Estimation", estimation_pass))
    except Exception as e:
        print(f"❌ Token Estimation test failed with exception: {e}")
        results.append(("Token Estimation", False))

    # Test 2: Token Limit Validation
    try:
        limit_pass = test_token_limit_validation()
        results.append(("Token Limit Validation", limit_pass))
    except Exception as e:
        print(f"❌ Token Limit Validation test failed with exception: {e}")
        results.append(("Token Limit Validation", False))

    # Test 3: Prompt Size Validation
    try:
        prompt_pass = test_prompt_size_validation()
        results.append(("Prompt Size Validation", prompt_pass))
    except Exception as e:
        print(f"❌ Prompt Size Validation test failed with exception: {e}")
        results.append(("Prompt Size Validation", False))

    # Test 4: Truncation
    try:
        truncation_pass = test_truncation()
        results.append(("Smart Truncation", truncation_pass))
    except Exception as e:
        print(f"❌ Smart Truncation test failed with exception: {e}")
        results.append(("Smart Truncation", False))

    # Summary
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 All C8 token validation tests passed!")
    else:
        print("\n⚠️  Some tests failed - please review the output above")

    return all_passed


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
