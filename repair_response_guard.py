import inspect

import response_guard
from execution_controller import ExecutionResult


print("=" * 70)
print("MINH MINI — RESPONSE GUARD DIAGNOSTIC")
print("=" * 70)


# ============================================================
# 1. SIGNATURE
# ============================================================

print("\n=== FUNCTIONS ===")

for name in (
    "validate_response",
    "guard_response",
    "safe_response",
):

    fn = getattr(
        response_guard,
        name,
        None,
    )

    print(f"\n--- {name} ---")

    if fn is None:
        print("MISSING")
        continue

    print("signature:", end=" ")

    try:
        print(inspect.signature(fn))
    except Exception as e:
        print("ERROR:", repr(e))


# ============================================================
# 2. SOURCE validate_response
# ============================================================

print("\n=== validate_response SOURCE ===")

try:
    print(
        inspect.getsource(
            response_guard.validate_response
        )
    )
except Exception as e:
    print("ERROR:", repr(e))


# ============================================================
# 3. SOURCE guard_response
# ============================================================

print("\n=== guard_response SOURCE ===")

try:
    print(
        inspect.getsource(
            response_guard.guard_response
        )
    )
except Exception as e:
    print("ERROR:", repr(e))


# ============================================================
# 4. TEST REALISTIC RESPONSES
# ============================================================

tests = [
    "Xin chào Lam!",
    "[FAKE CHAT] Xin chào Lam!",
    "[FAKE ACTION] open google",
    "[FAKE WEB] Đã tìm kiếm.",
    "ACTION_OK",
    "WEB_OK",
    "CHAT_OK",
    "",
]


print("\n=== RESPONSE TESTS ===")

for answer in tests:

    print("\nINPUT:", repr(answer))

    try:

        result = response_guard.validate_response(
            "test",
            answer,
            decision={
                "intent": "chat",
                "tool": "ollama",
            },
        )

        print(
            "type:",
            type(result),
        )

        print(
            "valid:",
            getattr(
                result,
                "valid",
                None,
            ),
        )

        print(
            "answer:",
            repr(
                getattr(
                    result,
                    "answer",
                    None,
                )
            ),
        )

        print(
            "changed:",
            getattr(
                result,
                "changed",
                None,
            ),
        )

        print(
            "blocked:",
            getattr(
                result,
                "blocked",
                None,
            ),
        )

        print(
            "reason:",
            repr(
                getattr(
                    result,
                    "reason",
                    None,
                )
            ),
        )

    except Exception as e:

        print(
            "EXCEPTION:",
            repr(e),
        )


# ============================================================
# 5. EXECUTION RESULT
# ============================================================

print("\n=== EXECUTION RESULT TEST ===")

execution_result = ExecutionResult(
    success=True,
    response="Xin chào Lam!",
    intent="chat",
    tool="ollama",
)

print(
    "execution_result:",
    execution_result,
)

try:

    result = response_guard.validate_response(
        "xin chào",
        execution_result.response,
        decision={
            "intent": execution_result.intent,
            "tool": execution_result.tool,
        },
        execution_result=execution_result,
    )

    print(
        "valid:",
        getattr(
            result,
            "valid",
            None,
        ),
    )

    print(
        "answer:",
        repr(
            getattr(
                result,
                "answer",
                None,
            )
        ),
    )

    print(
        "reason:",
        repr(
            getattr(
                result,
                "reason",
                None,
            )
        ),
    )

except Exception as e:

    print(
        "EXCEPTION:",
        repr(e),
    )


print("\n" + "=" * 70)
print("DIAGNOSTIC HOAN TAT")
print("=" * 70)