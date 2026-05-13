#
# Title: viewport.py
# Author: Matthew Smith 22173112
# Date: 20/03/26
# Purpose: 2D viewport for placing nodes, viewing mesh, panning and zooming
#

import math
import tkinter as tk
from enum import Enum

from gui.components.force_dialog import ForceDialog

from geometry.components.types import *
from geometry.manager import GeometryManager

UNITS = {
    "μm": dict(label="μm", mpu=1e-6, grid_step=1e-5, scale=1e8),
    "mm": dict(label="mm", mpu=1e-3, grid_step=1e-3, scale=1e3),
    "cm": dict(label="cm", mpu=1e-2, grid_step=1e-2, scale=1e2),
    "m":  dict(label="m",  mpu=1.0,  grid_step=1e-2, scale=1e2),
}

DEFAULT_UNIT   = "mm"
NODE_RADIUS_PX = 5
FORCE_ARROW_PX = 40
MIN_GRID_PX    = 8

class Tool(Enum):
    NODE       = 1
    FIXED_NODE = 2
    FORCE      = 3
    THERMAL    = 4

class Viewport(tk.Frame):

    def __init__(self, parent, geometry: GeometryManager, width=800, height=600):
        super().__init__(parent)

        self.geometry = geometry

        self._unit_key = DEFAULT_UNIT
        self._unit     = UNITS[DEFAULT_UNIT]
        self.grid_step = self._unit["grid_step"]
        self.scale     = self._unit["scale"]
        self.x_offset  = width  / 2
        self.y_offset  = height / 2
        self._init_w   = width
        self._init_h   = height
        self.tool        = Tool.NODE
        self._drag_start = None

        # Toolbar
        ctrl_bar = tk.Frame(self, bg="#f0f0f0", pady=2)
        ctrl_bar.pack(fill="x", side="top")
        tk.Label(ctrl_bar, text="Unit:", bg="#f0f0f0").pack(side="left", padx=(6, 2))
        self._unit_var = tk.StringVar(value=DEFAULT_UNIT)
        unit_menu = tk.OptionMenu(ctrl_bar, self._unit_var, *UNITS.keys(), command=self._on_unit_change)
        unit_menu.config(width=4)
        unit_menu.pack(side="left")
        tk.Label(ctrl_bar,
                 text="CONTROLS:  [R] Reset view   [1] Node   [2] Fixed   [3] Force   [4] Thermal BCs",
                 bg="#f0f0f0", fg="#666666", font=("Arial", 8)
                 ).pack(side="left", padx=8)

        # Canvas
        self.canvas = tk.Canvas(self, width=width, height=height, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<Button-1>",        self._on_left_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_left_click)
        self.canvas.bind("<ButtonPress-3>",   self._on_drag_start)
        self.canvas.bind("<B3-Motion>",       self._on_drag_motion)
        self.canvas.bind("<MouseWheel>",      self._on_mouse_wheel)
        self.canvas.bind("<Motion>",          self._on_mouse_move)
        self.canvas.bind("<Configure>",       lambda e: self._redraw())

        self.bind_all("1", lambda e: self._set_tool(Tool.NODE))
        self.bind_all("2", lambda e: self._set_tool(Tool.FIXED_NODE))
        self.bind_all("3", lambda e: self._set_tool(Tool.FORCE))
        self.bind_all("4", lambda e: self._set_tool(Tool.THERMAL))
        self.bind_all("r", lambda e: self._reset_view())

        self._redraw()

    ############################################################################
    # ---------- UNIT HELPERS ----------
    ############################################################################

    def _format_unit(self, metres):
        value = metres / self._unit["mpu"]
        return f"{round(value, 10):.6g}{self._unit['label']}"

    def _round_metres(self, metres):
        return f"{round(metres, 10):.8g}m"

    def _on_unit_change(self, key):
        self._unit_key = key
        self._unit     = UNITS[key]
        self.grid_step = self._unit["grid_step"]
        self._redraw()

    ############################################################################
    # ---------- TRANSFORMS ----------
    ############################################################################

    def world_to_screen(self, x, y):
        return (x * self.scale + self.x_offset, -y * self.scale + self.y_offset)

    def screen_to_world(self, px, py):
        return ((px - self.x_offset) / self.scale, -(py - self.y_offset) / self.scale)

    def snap(self, px, py):
        x, y = self.screen_to_world(px, py)
        gx = round(x / self.grid_step) * self.grid_step
        gy = round(y / self.grid_step) * self.grid_step
        return gx + 0.0, gy + 0.0

    ############################################################################
    # ---------- DRAWING ----------
    ############################################################################

    def _redraw(self):
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_elements()
        self._draw_forces()
        self._draw_nodes()

    def _draw_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        x0, y0 = self.screen_to_world(0, 0)
        x1, y1 = self.screen_to_world(w, h)

        x_min, x_max = min(x0, x1), max(x0, x1)
        y_min, y_max = min(y0, y1), max(y0, y1)
        minor_step = self.grid_step
        major_step = minor_step * 10

        if minor_step * self.scale >= MIN_GRID_PX:
            self._draw_grid_lines(x_min, x_max, y_min, y_max, minor_step, w, h, "#e8e8e8")
        if major_step * self.scale >= MIN_GRID_PX:
            self._draw_grid_lines(x_min, x_max, y_min, y_max, major_step, w, h, "#b8b8b8")
            self._draw_grid_labels(x_min, x_max, y_min, y_max, major_step)

        px0, _ = self.world_to_screen(0, 0)
        _,  py0 = self.world_to_screen(0, 0)
        self.canvas.create_line(px0, 0, px0, h, fill="#404040", width=2)
        self.canvas.create_line(0, py0, w, py0, fill="#404040", width=2)

    def _draw_grid_lines(self, x_min, x_max, y_min, y_max, step, w, h, colour):
        for x in self._frange(math.floor(x_min / step) * step, math.ceil(x_max / step) * step, step):
            px, _ = self.world_to_screen(x, 0)
            self.canvas.create_line(px, 0, px, h, fill=colour)
        for y in self._frange(math.floor(y_min / step) * step, math.ceil(y_max / step) * step, step):
            _, py = self.world_to_screen(0, y)
            self.canvas.create_line(0, py, w, py, fill=colour)

    def _draw_grid_labels(self, x_min, x_max, y_min, y_max, step):

        _, py0  = self.world_to_screen(0, 0)
        px0, _  = self.world_to_screen(0, 0)

        for x in self._frange(math.floor(x_min / step) * step, math.ceil(x_max / step) * step, step):
            if abs(x) < step * 0.01: continue
            px, _ = self.world_to_screen(x, 0)
            self.canvas.create_text(px, py0 + 2, text=self._format_unit(x), anchor="n", font=("Arial", 7), fill="#888888")

        for y in self._frange(math.floor(y_min / step) * step, math.ceil(y_max / step) * step, step):
            if abs(y) < step * 0.01: continue
            _, py = self.world_to_screen(0, y)
            self.canvas.create_text(px0 + 2, py, text=self._format_unit(y), anchor="w", font=("Arial", 7), fill="#888888")

    def _draw_nodes(self):
        r = NODE_RADIUS_PX
        for node in self.geometry.get_placed_nodes():
            px, py = self.world_to_screen(node.x, node.y)
            match node.type:
                case NodeType.NORMAL: self.canvas.create_oval(px-r, py-r, px+r, py+r, outline="black", width=2)
                case NodeType.FIXED:  self.canvas.create_oval(px-r, py-r, px+r, py+r, fill="black")
                case NodeType.FORCE:  self.canvas.create_oval(px-r, py-r, px+r, py+r, outline="red", width=2)

    def _draw_forces(self):
        for f in self.geometry.get_forces():
            x0, y0 = self.world_to_screen(f.node.x, f.node.y)
            rad = math.radians(f.angle)
            x1  = x0 + math.cos(rad) * FORCE_ARROW_PX
            y1  = y0 - math.sin(rad) * FORCE_ARROW_PX
            x2  = x1 + math.cos(rad) * FORCE_ARROW_PX
            y2  = y1 - math.sin(rad) * FORCE_ARROW_PX

            self.canvas.create_line(x0, y0, x1, y1, arrow=tk.LAST, fill="red", width=2)
            
            if(f.pxy == True): self.canvas.create_text(x1, y1, text="Pxy", fill="red", font=("Arial", 12, "bold"), anchor="sw")
            if(f.pz == True): self.canvas.create_text(x1, y1, text="Pz", fill="red", font=("Arial", 12, "bold"), anchor="sw")

            self.canvas.create_text(x2, y2, text=f"{f.magnitude}N", fill="red", font=("Arial", 10), anchor="sw")

    def _draw_elements(self):
        nodes = self.geometry.get_nodes()
        for e in self.geometry.get_elements():
            n1, n2, n3 = e.get_nodes(nodes)
            p1 = self.world_to_screen(n1.x, n1.y)
            p2 = self.world_to_screen(n2.x, n2.y)
            p3 = self.world_to_screen(n3.x, n3.y)
            self.canvas.create_line(*p1, *p2, fill="blue")
            self.canvas.create_line(*p2, *p3, fill="blue")
            self.canvas.create_line(*p3, *p1, fill="blue")

    def _draw_tooltip(self, px, py, node):
        self.canvas.delete("tooltip")
        text    = f"x={self._round_metres(node.x)}, y={self._round_metres(node.y)}\n{node.type.name}"
        text_id = self.canvas.create_text(px+10, py-10, text=text, anchor="sw", tags="tooltip")
        bbox = self.canvas.bbox(text_id)
        if bbox:
            self.canvas.create_rectangle(
                bbox[0]-3, bbox[1]-3, bbox[2]+3, bbox[3]+3,
                fill="lightyellow", outline="gray", tags="tooltip"
            )
            self.canvas.tag_raise(text_id)

    ############################################################################
    # ---------- INPUT HANDLERS ----------
    ############################################################################

    def _on_left_click(self, event):
        x, y = self.snap(event.x, event.y)
        if self.geometry.node_exists_at(x, y): return

        match self.tool:
            case Tool.NODE:
                self.geometry.add_node(Node(x, y, NodeType.NORMAL))

            case Tool.FIXED_NODE:
                self.geometry.add_node(Node(x, y, NodeType.FIXED))

            case Tool.FORCE:
                dlg = ForceDialog(self, "Define Force")
                if dlg.magnitude is None or dlg.angle is None: return
                node = Node(x, y, NodeType.FORCE)
                self.geometry.add_node(node)
                self.geometry.add_force(Force(node, magnitude=dlg.magnitude, angle=dlg.angle, pxy=dlg.is_pxy, pz=dlg.is_pz))

            case Tool.THERMAL:
                print("YAY")

        self.geometry.update()
        self._redraw()

    def _on_double_left_click(self, event):
        x, y = self.snap(event.x, event.y)
        self.geometry.remove_node_at(x, y)
        self.geometry.update()
        self._redraw()

    def _on_mouse_move(self, event):

        if(self.tool == Tool.THERMAL): pass

        node = self._find_nearest_node(event.x, event.y)
        if node: self._draw_tooltip(event.x, event.y, node)
        else:
            x, y = self.snap(event.x, event.y)
            self.canvas.delete("tooltip")
            self.canvas.create_text(
                event.x + 10, event.y - 10,
                text=f"x={self._round_metres(x)}, y={self._round_metres(y)}",
                anchor="sw", tags="tooltip", fill="#888888", font=("Arial", 8)
            )

    def _on_drag_start(self, event):
        self._drag_start = (event.x, event.y)

    def _on_drag_motion(self, event):
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self.x_offset   += dx
        self.y_offset   += dy
        self._drag_start = (event.x, event.y)
        self._redraw()

    def _on_mouse_wheel(self, event):
        factor        = 1.1 if event.delta > 0 else 0.9
        self.x_offset = event.x - factor * (event.x - self.x_offset)
        self.y_offset = event.y - factor * (event.y - self.y_offset)
        self.scale   *= factor
        self._redraw()

    ############################################################################
    # ---------- UTILITY ----------
    ############################################################################

    def _frange(self, start, stop, step):
        if step == 0: return
        x = start
        if start <= stop:
            while x <= stop + step * 1e-9:
                yield x
                x += step
        else:
            while x >= stop - step * 1e-9:
                yield x
                x -= step

    def _find_nearest_node(self, px, py):
        radius_px = NODE_RADIUS_PX + 4
        for node in self.geometry.get_placed_nodes():
            npx, npy = self.world_to_screen(node.x, node.y)
            dx, dy = npx - px, npy - py
            if dx*dx + dy*dy <= radius_px * radius_px:
                return node
        return None

    def _set_tool(self, t: Tool)  -> None: self.tool = t

    def _reset_view(self) -> None:
        self.scale    = self._unit["scale"]
        self.x_offset = self._init_w / 2
        self.y_offset = self._init_h / 2
        self._redraw()

    def regenerate(self) -> None:
        self.geometry.update()
        self._redraw()

    ############################################################################
    # ---------- PUBLIC API ----------
    ############################################################################

    def clear(self) -> None:
        self.geometry.clear()
        self._redraw()