"""Utility helpers for human-like interactions."""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, fields
from typing import Any, Dict, Optional, Tuple

from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


@dataclass
class HumanMouseConfig:
    """Configuration container for human-like mouse actions."""

    enabled: bool = False
    min_steps: int = 10
    max_steps: int = 24
    min_step_duration_ms: int = 12
    max_step_duration_ms: int = 36
    min_pause: float = 0.01
    max_pause: float = 0.05
    path_jitter: float = 0.7
    target_jitter: float = 2.5
    overshoot_chance: float = 0.2
    overshoot_range: Tuple[float, float] = (1.5, 4.0)
    seed: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "HumanMouseConfig":
        if not data:
            return cls()

        kwargs: Dict[str, Any] = {}
        for field in fields(cls):
            if field.name not in data:
                continue
            value = data[field.name]
            if field.name == "overshoot_range" and isinstance(value, (list, tuple)) and len(value) == 2:
                value = (float(value[0]), float(value[1]))
            kwargs[field.name] = value
        if "enabled" not in kwargs:
            kwargs["enabled"] = True
        return cls(**kwargs)


class HumanMouse:
    """Generates human-like pointer trajectories using W3C actions."""

    def __init__(
        self,
        driver: WebDriver,
        config: HumanMouseConfig,
        logger=None,
    ) -> None:
        self.driver = driver
        self.config = config
        self.logger = logger
        self._rand = random.Random(config.seed)
        self._last_position: Optional[Tuple[float, float]] = None

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    def move_to(self, element: WebElement, description: str = "") -> None:
        try:
            self._move(element, description=description, perform_click=False)
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"人类化移动失败，回退到原生move_to_element: {exc}")
            self._fallback_move(element)

    def click(self, element: WebElement, description: str = "") -> None:
        try:
            self._move(element, description=description, perform_click=True)
        except Exception as exc:
            if self.logger:
                self.logger.warning(f"人类化点击失败，回退到原生click: {exc}")
            element.click()

    def _move(
        self,
        element: WebElement,
        description: str = "",
        perform_click: bool = False,
    ) -> None:
        config = self.config
        steps = self._choose_step_count()
        viewport_width, viewport_height = self._viewport_size()

        if self._last_position:
            start_x, start_y = self._last_position
        else:
            start_x = self._rand.uniform(viewport_width * 0.1, viewport_width * 0.9)
            start_y = self._rand.uniform(viewport_height * 0.1, viewport_height * 0.9)

        target_x, target_y = self._choose_target_point(element)

        builder = ActionBuilder(self.driver)
        pointer = builder.add_pointer_input("mouse", "human-pointer")

        pointer.create_pointer_move(duration=0, x=start_x, y=start_y, origin="viewport")
        pointer.create_pause(self._rand.uniform(config.min_pause, config.max_pause))

        current_x, current_y = start_x, start_y
        distance_x = target_x - start_x
        distance_y = target_y - start_y
        path_length = 0.0
        segments = 0
        overshoot_used = False
        start_time = time.perf_counter()

        for step_index in range(1, steps):
            progress = step_index / steps
            eased = self._ease_in_out(progress)
            point_x = start_x + distance_x * eased
            point_y = start_y + distance_y * eased
            point_x += self._rand.uniform(-config.path_jitter, config.path_jitter)
            point_y += self._rand.uniform(-config.path_jitter, config.path_jitter)

            seg_dx = point_x - current_x
            seg_dy = point_y - current_y
            path_length += math.hypot(seg_dx, seg_dy)
            segments += 1
            self._move_pointer(pointer, current_x, current_y, point_x, point_y)
            current_x, current_y = point_x, point_y
            pointer.create_pause(self._rand.uniform(config.min_pause, config.max_pause))

        if self._rand.random() < config.overshoot_chance:
            overshoot_distance = self._rand.uniform(*config.overshoot_range)
            angle = self._rand.uniform(0, 2 * math.pi)
            overshoot_x = target_x + math.cos(angle) * overshoot_distance
            overshoot_y = target_y + math.sin(angle) * overshoot_distance
            seg_dx = overshoot_x - current_x
            seg_dy = overshoot_y - current_y
            path_length += math.hypot(seg_dx, seg_dy)
            segments += 1
            self._move_pointer(pointer, current_x, current_y, overshoot_x, overshoot_y)
            current_x, current_y = overshoot_x, overshoot_y
            pointer.create_pause(self._rand.uniform(config.min_pause, config.max_pause))
            overshoot_used = True

        seg_dx = target_x - current_x
        seg_dy = target_y - current_y
        path_length += math.hypot(seg_dx, seg_dy)
        segments += 1
        self._move_pointer(pointer, current_x, current_y, target_x, target_y)
        pointer.create_pause(self._rand.uniform(config.min_pause, config.max_pause))

        if perform_click:
            pointer.create_pointer_down(button=0)
            pointer.create_pause(self._rand.uniform(config.min_pause, config.max_pause))
            pointer.create_pointer_up(button=0)

        builder.perform()
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        avg_speed = path_length / (elapsed_ms / 1000) if elapsed_ms > 0 else 0.0

        if self.logger:
            label = description or self._safe_element_label(element)
            action = "点击" if perform_click else "移动"
            self.logger.info(
                f"[HumanMouse] action={action} target={label} steps={segments}"
                f" duration={elapsed_ms:.1f}ms path={path_length:.1f}px"
                f" speed={avg_speed:.1f}px/s overshoot={overshoot_used}"
            )

        self._last_position = (target_x, target_y)

    def _choose_target_point(self, element: WebElement) -> Tuple[float, float]:
        rect = element.rect
        base_x = float(rect.get("x", 0.0)) + float(rect.get("width", 0.0)) / 2.0
        base_y = float(rect.get("y", 0.0)) + float(rect.get("height", 0.0)) / 2.0

        jitter = self.config.target_jitter
        if jitter > 0:
            base_x += self._rand.uniform(-jitter, jitter)
            base_y += self._rand.uniform(-jitter, jitter)
        return base_x, base_y

    def _move_pointer(
        self,
        pointer: PointerInput,
        current_x: float,
        current_y: float,
        target_x: float,
        target_y: float,
    ) -> None:
        duration_ms = self._rand.randint(
            self.config.min_step_duration_ms, self.config.max_step_duration_ms
        )
        delta_x = target_x - current_x
        delta_y = target_y - current_y
        pointer.create_pointer_move(
            duration=duration_ms,
            x=delta_x,
            y=delta_y,
            origin="pointer",
        )

    def _ease_in_out(self, t: float) -> float:
        t = max(0.0, min(1.0, t))
        return t * t * (3 - 2 * t)

    def _safe_element_label(self, element: WebElement) -> str:
        try:
            outer = element.get_attribute("outerHTML")
            if outer:
                return outer[:60]
        except Exception:
            pass
        try:
            return f"<{element.tag_name}>"
        except Exception:
            return "target element"

    def _choose_step_count(self) -> int:
        config = self.config
        if config.min_steps > config.max_steps:
            return config.min_steps
        return self._rand.randint(config.min_steps, config.max_steps)

    def _viewport_size(self) -> Tuple[float, float]:
        viewport = self.driver.execute_script(
            "return {width: window.innerWidth || 0, height: window.innerHeight || 0};"
        )
        viewport_width = max(1.0, float(viewport.get("width", 1)))
        viewport_height = max(1.0, float(viewport.get("height", 1)))
        return viewport_width, viewport_height

    def _fallback_move(self, element: WebElement) -> None:
        try:
            from selenium.webdriver import ActionChains

            ActionChains(self.driver).move_to_element(element).perform()
        except Exception:
            pass
