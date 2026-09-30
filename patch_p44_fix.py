import ast
import shutil
from pathlib import Path

MAIN = Path("main.py")
BACKUP = Path("main_execution_contract_p44_fix_before.py")

print("=== P4-4 CONTRACT CONTEXT FIX ===")

source = MAIN.read_text(encoding="utf-8")
ast.parse(source)

tree = ast.parse(source)

core = [
    node for node in tree.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

process = [
    node for node in core.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

lines = source.splitlines()

start = process.lineno - 1
end = process.end_lineno

section = lines[start:end]

# ------------------------------------------------------------
# Find P4-4 build
# ------------------------------------------------------------

build_indexes = [
    i for i, line in enumerate(section)
    if "# EXECUTION_CONTRACT_P44_BUILD" in line
]

if len(build_indexes) != 1:
    raise RuntimeError(
        f"P4-4 build marker count = {len(build_indexes)}"
    )

build_index = build_indexes[0]

# ------------------------------------------------------------
# Check existing fix not already present
# ------------------------------------------------------------

if "contract_decision = decision" in source:
    raise RuntimeError(
        "P4-4 contract context fix already exists."
    )

print("EXISTING CHECK: PASS")

# ------------------------------------------------------------
# Find contract build call
# ------------------------------------------------------------

build_call_indexes = [
    i for i, line in enumerate(section)
    if "execution_contract = self.execution_contract_builder.build(" in line
]

if len(build_call_indexes) != 1:
    raise RuntimeError(
        "Cannot uniquely locate execution contract build."
    )

call_index = build_call_indexes[0]

# The call is:
#
# execution_contract = builder.build(
#     completed,
#     meta_result,
# )
#
# We replace ONLY the argument `meta_result`
# with a preserved execution-context object.
#
# Instead of reconstructing MetaOrchestrator manually,
# use the original Brain/Think result to preserve the
# action intent before Main converts it to clarification.

# ------------------------------------------------------------
# Insert contract_decision / contract_meta preparation
# ------------------------------------------------------------

build_line = section[call_index]

indent = build_line[
    :len(build_line) - len(build_line.lstrip())
]

prep = [
    indent + "# EXECUTION_CONTRACT_P44_CONTEXT_FIX",
    indent + "contract_meta = meta_result",
    indent + "try:",
    indent + "    original_intent = get_decision_value(",
    indent + "        decision,",
    indent + "        'intent',",
    indent + "        '',",
    indent + "    )",
    indent + "    original_action = get_decision_value(",
    indent + "        decision,",
    indent + "        'action',",
    indent + "        '',",
    indent + "    )",
    indent + "    original_target = get_decision_value(",
    indent + "        decision,",
    indent + "        'target',",
    indent + "        '',",
    indent + "    )",
    indent + "    original_missing = get_decision_value(",
    indent + "        decision,",
    indent + "        'missing',",
    indent + "        [],",
    indent + "    )",
    indent + "    original_needs_clarification = get_decision_value(",
    indent + "        decision,",
    indent + "        'needs_clarification',",
    indent + "        False,",
    indent + "    )",
    indent + "    if original_intent == 'clarification':",
    indent + "        original_intent = get_decision_value(",
    indent + "            getattr(self, 'last_think_x', None),",
    indent + "            'intent',",
    indent + "            '',",
    indent + "        )",
    indent + "        original_action = get_decision_value(",
    indent + "            getattr(self, 'last_think_x', None),",
    indent + "            'action',",
    indent + "            '',",
    indent + "        )",
    indent + "        original_target = get_decision_value(",
    indent + "            getattr(self, 'last_think_x', None),",
    indent + "            'target',",
    indent + "            '',",
    indent + "        )",
    indent + "        original_missing = get_decision_value(",
    indent + "            getattr(self, 'last_think_x', None),",
    indent + "            'missing',",
    indent + "            [],",
    indent + "        )",
    indent + "        original_needs_clarification = True",
    indent + "    if original_intent in {",
    indent + "        'action',",
    indent + "        'web',",
    indent + "        'memory',",
    indent + "        'time',",
    indent + "        'date',",
    indent + "    } and original_needs_clarification:",
    indent + "        contract_meta = {",
    indent + "            'intent': original_intent,",
    indent + "            'action': original_action,",
    indent + "            'target': original_target,",
    indent + "            'missing': original_missing,",
    indent + "            'mode': 'clarify',",
    indent + "            'next_step': 'clarify',",
    indent + "            'tool': (",
    indent + "                'action'",
    indent + "                if original_intent == 'action'",
    indent + "                else (",
    indent + "                    'web'",
    indent + "                    if original_intent == 'web'",
    indent + "                    else (",
    indent + "                        'memory'",
    indent + "                        if original_intent == 'memory'",
    indent + "                        else (",
    indent + "                            'system_time'",
    indent + "                            if original_intent == 'time'",
    indent + "                            else 'system_date'",
    indent + "                        )",
    indent + "                    )",
    indent + "                )",
    indent + "            ),",
    indent + "            'constraints': [",
    indent + "                'clarification_required',",
    indent + "                'missing_information',",
    indent + "            ],",
    indent + "        }",
    indent + "except Exception as exc:",
    indent + "    contract_meta = meta_result",
    indent + "    log(",
    indent + '        "EXECUTION CONTRACT CONTEXT ERROR: "',
    indent + "        + repr(exc)",
    indent + "    )",
    "",
]

absolute_insert = start + call_index

new_lines = list(lines)

new_lines[
    absolute_insert:absolute_insert
] = prep

# ------------------------------------------------------------
# Re-find process after insertion
# ------------------------------------------------------------

new_source = "\n".join(new_lines) + "\n"
ast.parse(new_source)

tree2 = ast.parse(new_source)

core2 = [
    node for node in tree2.body
    if isinstance(node, ast.ClassDef)
    and node.name == "MinhMiniCore"
][0]

process2 = [
    node for node in core2.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "process"
][0]

lines2 = new_source.splitlines()

start2 = process2.lineno - 1
end2 = process2.end_lineno

section2 = lines2[start2:end2]

# ------------------------------------------------------------
# Replace ONLY build argument
# ------------------------------------------------------------

call_indexes = [
    i for i, line in enumerate(section2)
    if "execution_contract = self.execution_contract_builder.build(" in line
]

if len(call_indexes) != 1:
    raise RuntimeError(
        "Final contract build call is not unique."
    )

call_index2 = call_indexes[0]

argument_indexes = [
    i for i, line in enumerate(section2)
    if i > call_index2
    and line.strip() == "meta_result,"
]

if len(argument_indexes) != 1:
    raise RuntimeError(
        "Could not uniquely locate meta_result contract argument."
    )

argument_index = argument_indexes[0]

absolute_argument = start2 + argument_index

new_lines[
    absolute_argument
] = (
    new_lines[absolute_argument]
    .replace(
        "meta_result,",
        "contract_meta,",
    )
)

final_source = "\n".join(new_lines) + "\n"

# ------------------------------------------------------------
# Final AST
# ------------------------------------------------------------

ast.parse(final_source)

print("FINAL AST: PASS")

# ------------------------------------------------------------
# Marker checks
# ------------------------------------------------------------

markers = [
    "# EXECUTION_CONTRACT_P44_CONTEXT_FIX",
    "contract_meta = meta_result",
    "original_intent",
    "original_needs_clarification",
    "contract_meta = {",
    "clarification_required",
    "execution_contract = self.execution_contract_builder.build(",
    "contract_meta,",
]

for marker in markers:
    if marker not in final_source:
        raise RuntimeError(
            "MARKER CHECK FAILED: " + marker
        )
    print(
        "CHECK:",
        marker,
        "= PASS",
    )

# ------------------------------------------------------------
# Backup
# ------------------------------------------------------------

shutil.copy2(MAIN, BACKUP)

if not BACKUP.exists():
    raise RuntimeError("Backup creation failed.")

print("BACKUP: PASS")
print("BACKUP FILE:", BACKUP.name)

# ------------------------------------------------------------
# Write
# ------------------------------------------------------------

MAIN.write_text(
    final_source,
    encoding="utf-8",
)

print("PATCH STATUS: PASS")
print("MAIN.PY UPDATED")
print("BACKUP:", BACKUP.name)
