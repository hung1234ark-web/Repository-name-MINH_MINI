import inspect
import traceback

import main


def show(label, value):
    print()
    print("=" * 70)
    print(label)
    print("=" * 70)
    print(value)


def get_brain_callable():
    minh = getattr(main, "MINH", None)

    if minh is not None:
        method = getattr(minh, "brain_think", None)

        if callable(method):
            return method

        brain = getattr(minh, "brain", None)

        if brain is not None:
            think = getattr(brain, "think", None)

            if callable(think):
                return think

    fn = getattr(main, "brain_think", None)

    if callable(fn):
        try:
            signature = inspect.signature(fn)
            params = list(signature.parameters.values())

            if params and params[0].name == "self":
                if minh is not None:
                    return fn.__get__(
                        minh,
                        type(minh),
                    )

            return fn

        except Exception:
            return fn

    brain_module = getattr(
        main,
        "brain_module",
        None,
    )

    if brain_module is not None:
        think = getattr(
            brain_module,
            "think",
            None,
        )

        if callable(think):
            return think

    raise RuntimeError(
        "Không tìm thấy Brain callable."
    )


def call_brain(message):
    brain_fn = get_brain_callable()

    print(
        "Brain callable:",
        brain_fn,
    )

    print(
        "Brain signature:",
        inspect.signature(brain_fn),
    )

    return brain_fn(message)


def get_handlers():
    build_handlers = getattr(
        main,
        "build_handlers",
        None,
    )

    if not callable(build_handlers):
        raise RuntimeError(
            "Không tìm thấy build_handlers()."
        )

    print(
        "build_handlers signature:",
        inspect.signature(build_handlers),
    )

    return build_handlers()


def get_controller():
    controller = getattr(
        main,
        "controller",
        None,
    )

    if controller is not None:
        print(
            "Controller lấy từ main.controller"
        )
        return controller

    create_controller = getattr(
        main,
        "create_controller",
        None,
    )

    if not callable(create_controller):
        raise RuntimeError(
            "Không tìm thấy create_controller()."
        )

    signature = inspect.signature(
        create_controller
    )

    print(
        "create_controller signature:",
        signature,
    )

    handlers = get_handlers()

    print(
        "Handlers:",
        sorted(handlers.keys()),
    )

    kwargs = {}

    if "handlers" in signature.parameters:
        kwargs["handlers"] = handlers

    return create_controller(
        **kwargs
    )


def run_case(message):
    print()
    print("#" * 70)
    print(f"INPUT: {message}")
    print("#" * 70)

    try:
        # -------------------------------------------------
        # BRAIN
        # -------------------------------------------------

        decision = call_brain(message)

        show(
            "BRAIN DECISION",
            decision,
        )

        # -------------------------------------------------
        # ROUTER
        # -------------------------------------------------

        route_fn = getattr(
            main,
            "route_decision",
            None,
        )

        if not callable(route_fn):
            raise RuntimeError(
                "Không tìm thấy route_decision()."
            )

        print(
            "Router signature:",
            inspect.signature(route_fn),
        )

        route = route_fn(
            message,
            decision,
        )

        show(
            "ROUTER RESULT",
            route,
        )

        # -------------------------------------------------
        # CONTROLLER
        # -------------------------------------------------

        controller = get_controller()

        print(
            "Controller:",
            controller,
        )

        execute = getattr(
            controller,
            "execute",
            None,
        )

        if not callable(execute):
            raise RuntimeError(
                "Controller không có execute()."
            )

        print(
            "Controller.execute:",
            inspect.signature(execute),
        )

        signature = inspect.signature(
            execute
        )

        kwargs = {}

        if "message" in signature.parameters:
            kwargs["message"] = message

        if "decision" in signature.parameters:
            kwargs["decision"] = decision

        result = execute(
            **kwargs
        )

        show(
            "CONTROLLER RESULT",
            result,
        )

        response = getattr(
            result,
            "response",
            None,
        )

        if response is None:
            response = str(result)

        print(
            "FINAL RESPONSE:",
            repr(response),
        )

        return True

    except Exception as exc:
        print()
        print(
            "[FAIL] FLOW ERROR:",
            repr(exc),
        )

        traceback.print_exc()

        return False


def main_test():
    print()
    print("=" * 70)
    print("MINH MINI — FINAL REAL FLOW TEST")
    print("=" * 70)

    print(
        "MINH:",
        getattr(main, "MINH", None),
    )

    print(
        "MinhMiniCore:",
        getattr(main, "MinhMiniCore", None),
    )

    print(
        "brain_think:",
        getattr(main, "brain_think", None),
    )

    cases = [
        "xin chào Minh",
        "mở Google",
        "tìm giá iPhone",
        "nhớ Lam đang học Python",
    ]

    passed = 0

    for message in cases:
        if run_case(message):
            passed += 1

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        f"PASS: {passed}/{len(cases)}"
    )

    if passed == len(cases):
        print(
            ">>> FINAL REAL FLOW TEST: PASS"
        )
    else:
        print(
            ">>> FINAL REAL FLOW TEST: NEED FIX"
        )


if __name__ == "__main__":
    main_test()