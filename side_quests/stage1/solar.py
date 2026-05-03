import math
import os
import sys

import pygame

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.state import State
from util.const import SCREEN_SIZE

SKY_TOP = (24, 26, 36)
SKY_BOTTOM = (10, 12, 18)
RAY_GLOW = (255, 232, 150)
RAY_CORE = (255, 250, 214)
RED_RAY = (255, 90, 90)
BLUE_RAY = (80, 155, 255)
ORANGE_RAY = (255, 165, 90)
YELLOW_RAY = (255, 220, 120)
GREEN_RAY = (120, 220, 140)
CYAN_RAY = (90, 210, 230)
VIOLET_RAY = (170, 120, 255)
PLANT_GREEN = (84, 188, 120)
PANEL_LIGHT = (66, 140, 156)
MIRROR_COLOR = (230, 232, 238)
MIRROR_FRAME = (178, 132, 86)
PRISM_COLOR = (200, 220, 255)
PRISM_FRAME = (100, 150, 200)
UI_TEXT = (235, 232, 220)
UI_BG = (18, 20, 26)
ACCENT = (255, 182, 94)
CAVE_WALL = (28, 28, 34)
CAVE_FLOOR = (42, 36, 30)
TORCH_COLOR = (255, 210, 140)

MAX_RAY_SPLITS = 1

SPECTRUM = [
    ("red",    RED_RAY,    1.515),
    ("orange", ORANGE_RAY, 1.520),
    ("yellow", YELLOW_RAY, 1.525),
    ("green",  GREEN_RAY,  1.530),
    ("cyan",   CYAN_RAY,   1.535),
    ("blue",   BLUE_RAY,   1.540),
    ("violet", VIOLET_RAY, 1.545),
]

RAY_COLORS = {
    "white":  (RAY_GLOW,    RAY_CORE),
    "red":    (RED_RAY,     (255, 110, 110)),
    "orange": (ORANGE_RAY,  (255, 190, 120)),
    "yellow": (YELLOW_RAY,  (255, 240, 170)),
    "green":  (GREEN_RAY,   (150, 240, 170)),
    "cyan":   (CYAN_RAY,    (140, 240, 255)),
    "blue":   (BLUE_RAY,    (110, 190, 255)),
    "violet": (VIOLET_RAY,  (200, 150, 255)),
}

def _cross2(v1, v2):
    return v1.x * v2.y - v1.y * v2.x

def _ray_segment_intersection(origin, direction, seg_a, seg_b):
    """Return (t, point) for the first forward intersection, or None."""
    r = direction
    s = seg_b - seg_a
    rxs = _cross2(r, s)
    if abs(rxs) < 1e-9:
        return None
    q_p = seg_a - origin
    t = _cross2(q_p, s) / rxs
    u = _cross2(q_p, r) / rxs
    if t > 1e-5 and 0.0 <= u <= 1.0:
        return t, origin + r * t
    return None

def _reflect(direction, normal):
    """Specular reflection. normal must face toward the incoming ray."""
    n = normal.normalize()
    d = direction.normalize()
    return (d - 2.0 * d.dot(n) * n).normalize()

def _refract(direction, outward_normal, n1, n2):
    """Snell's law refraction.

    outward_normal points away from the surface into the medium the incoming
    ray travels in.  Returns None on total internal reflection.
    """
    d = direction.normalize()
    n = outward_normal.normalize()

    cos_i = -d.dot(n)
    if cos_i < 0.0:
        n = -n
        cos_i = -cos_i

    eta = n1 / n2
    sin2_t = eta * eta * (1.0 - cos_i * cos_i)
    if sin2_t > 1.0:
        return None
    cos_t = math.sqrt(max(0.0, 1.0 - sin2_t))
    return (eta * d + (eta * cos_i - cos_t) * n).normalize()

def _edge_outward_normal(a, b, interior):
    """Unit normal of edge (a→b) pointing away from interior."""
    edge = (b - a).normalize()
    n = pygame.Vector2(-edge.y, edge.x)
    mid = (a + b) * 0.5
    if (mid - interior).dot(n) < 0:
        n = -n
    return n

def _nudge(pt, direction, eps=1.0):
    return pt + direction * eps

def _prism_points(center, size, angle_deg=0.0):
    top   = pygame.Vector2(center.x,               center.y - size)
    right = pygame.Vector2(center.x + size * 0.95,  center.y + size * 0.75)
    left  = pygame.Vector2(center.x - size * 0.95,  center.y + size * 0.75)
    pts = [top, right, left]
    if abs(angle_deg) > 1e-6:
        rad = math.radians(angle_deg)
        s, c = math.sin(rad), math.cos(rad)
        def rot(p):
            r = p - center
            return pygame.Vector2(r.x*c - r.y*s, r.x*s + r.y*c) + center
        pts = [rot(p) for p in pts]
    return pts

def _prism_edges(points):
    n = len(points)
    return [(points[i], points[(i+1) % n], i) for i in range(n)]

def _ray_enter_prism(origin, direction, prism):
    """Find the closest entry hit on the prism boundary.

    Only returns hits where the ray travels INTO the solid (outward normal
    opposes the ray), so a ray exiting the prism never re-triggers entry.
    """
    pts    = _prism_points(prism["center"], prism["size"], prism.get("angle", 0.0))
    center = prism["center"]
    best_t = 1e18
    best   = None
    for a, b, idx in _prism_edges(pts):
        hit = _ray_segment_intersection(origin, direction, a, b)
        if hit is None:
            continue
        t, point = hit
        if t >= best_t:
            continue
        n_out = _edge_outward_normal(a, b, center)
        if direction.dot(n_out) >= 0:
            continue
        best_t = t
        best = {
            "t": t,
            "point": point,
            "normal_out": n_out,
            "edge_index": idx,
            "prism_points": pts,
            "prism_center": center,
        }
    return best

def _trace_through_prism(entry_hit, direction, n_glass):
    """Trace a ray from prism entry to exit (handling TIR bounces).

    Returns (exit_point, exit_direction, [(seg_start, seg_end), ...])
    or None if the ray is lost.
    """
    pts      = entry_hit["prism_points"]
    center   = entry_hit["prism_center"]
    n_in     = entry_hit["normal_out"]

    refracted = _refract(direction, n_in, 1.0, n_glass)
    if refracted is None:
        return None  # shouldn't happen from air but be safe

    internal_segs = []
    cur_origin = _nudge(entry_hit["point"], refracted)
    cur_dir    = refracted
    skip_idx   = entry_hit["edge_index"]

    for _ in range(8):
        best_t   = 1e18
        exit_hit = None
        for a, b, idx in _prism_edges(pts):
            if idx == skip_idx:
                continue
            hit = _ray_segment_intersection(cur_origin, cur_dir, a, b)
            if hit is None:
                continue
            t, point = hit
            if t < best_t:
                best_t   = t
                n_out    = _edge_outward_normal(a, b, center)
                exit_hit = {"point": point, "normal_out": n_out, "edge_index": idx}

        if exit_hit is None:
            return None

        internal_segs.append((cur_origin, exit_hit["point"]))

        n_exit    = exit_hit["normal_out"]
        exit_dir  = _refract(cur_dir, -n_exit, n_glass, 1.0)

        if exit_dir is not None:
            exit_pt = _nudge(exit_hit["point"], exit_dir)
            return exit_pt, exit_dir, internal_segs

        tir_dir  = _reflect(cur_dir, -n_exit)
        skip_idx = exit_hit["edge_index"]
        cur_origin = _nudge(exit_hit["point"], tir_dir)
        cur_dir    = tir_dir

    return None

class Mirror:
    def __init__(self, center, length, angle_deg, min_angle=-80.0, max_angle=80.0):
        self.center    = pygame.Vector2(center)
        self.length    = length
        self.angle_deg = angle_deg
        self.min_angle = min_angle
        self.max_angle = max_angle

    def rotate(self, delta_deg):
        self.angle_deg = max(self.min_angle, min(self.max_angle, self.angle_deg + delta_deg))

    def endpoints(self):
        rad = math.radians(self.angle_deg)
        dx  = math.cos(rad) * self.length * 0.5
        dy  = math.sin(rad) * self.length * 0.5
        return (pygame.Vector2(self.center.x - dx, self.center.y - dy),
                pygame.Vector2(self.center.x + dx, self.center.y + dy))

    def outward_normal(self, ray_dir):
        """Normal that faces the incoming ray."""
        a, b = self.endpoints()
        edge = (b - a).normalize()
        n = pygame.Vector2(-edge.y, edge.x)
        return n if n.dot(-ray_dir) > 0 else -n

    def hit_test(self, point, radius=28):
        return self.center.distance_to(point) <= radius

def _load_fonts():
    base_dir  = os.path.dirname(__file__)
    font_path = os.path.join(base_dir, "..", "assets", "Feathergraphy_Clean.ttf")
    if os.path.exists(font_path):
        return {
            "title": pygame.font.Font(font_path, 36),
            "ui":    pygame.font.Font(font_path, 20),
            "small": pygame.font.Font(font_path, 16),
        }
    return {
        "title": pygame.font.SysFont(None, 36, bold=True),
        "ui":    pygame.font.SysFont(None, 20),
        "small": pygame.font.SysFont(None, 16),
    }

def _lerp_color(a, b, t):
    return (int(a[0]+(b[0]-a[0])*t),
            int(a[1]+(b[1]-a[1])*t),
            int(a[2]+(b[2]-a[2])*t))

def _draw_vertical_gradient(screen, top_color, bottom_color):
    w, h = screen.get_size()
    for y in range(h):
        pygame.draw.line(screen, _lerp_color(top_color, bottom_color, y/(h-1)),
                         (0, y), (w, y))

class Solar(State):
    def __init__(self, screen_size=SCREEN_SIZE):
        super().__init__()
        self.screen_size = screen_size
        self.width, self.height = screen_size
        self.fonts          = _load_fonts()
        self.selected_index = 0
        self.mirrors        = self._create_mirrors()
        self.prisms         = self._create_prisms()
        self.sun_origin     = pygame.Vector2(self.width * 0.15, 40)
        self.sun_angle_deg  = 25
        self.max_bounces    = 8
        self.max_ray_dist   = math.hypot(self.width, self.height) * 2
        self.red_target     = pygame.Rect(80, self.height - 140, 160, 100)
        self.blue_target    = pygame.Rect(self.width - 240, self.height - 140, 160, 100)
        self.ray_segments   = []
        self.red_charge     = 0.0
        self.blue_charge    = 0.0
        self.win            = False
        self.last_update_ms = pygame.time.get_ticks()
        self.dragging_prism  = None
        self.dragging_mirror = None
        self.drag_offset     = pygame.Vector2(0, 0)
        self.last_mouse_pos  = None

    def _create_mirrors(self):
        lx, rx = 120, self.width - 120
        ys = [150, 260, 370]
        return ([Mirror((lx, y), 120, -25 + i*10) for i, y in enumerate(ys)] +
                [Mirror((rx, y), 120,  25 - i*10) for i, y in enumerate(ys)])

    def _create_prisms(self):
        return [
            {"center": pygame.Vector2(self.width*0.3, 200), "size": 40, "angle": 0.0},
            {"center": pygame.Vector2(self.width*0.7, 280), "size": 40, "angle": 0.0},
        ]

    def _reset(self):
        self.mirrors = self._create_mirrors()
        self.prisms  = self._create_prisms()
        self.selected_index  = 0
        self.red_charge      = 0.0
        self.blue_charge     = 0.0
        self.win             = False
        self.dragging_prism  = None
        self.dragging_mirror = None
        self.last_mouse_pos  = None

    def _find_prism_at(self, pos):
        for i, p in enumerate(self.prisms):
            if p["center"].distance_to(pos) <= p["size"]:
                return i
        return None

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER) and (event.mod & pygame.KMOD_CTRL):
                self.red_charge = 100.0
                self.blue_charge = 100.0
                self.win = True
                self.done = True
                return
            if k == pygame.K_ESCAPE:
                self.quit = True
            elif k in (pygame.K_TAB, pygame.K_DOWN):
                self.selected_index = (self.selected_index + 1) % len(self.mirrors)
            elif k == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.mirrors)
            elif pygame.K_1 <= k <= pygame.K_6:
                self.selected_index = k - pygame.K_1
            elif k in (pygame.K_LEFT, pygame.K_a):
                self.mirrors[self.selected_index].rotate(-4)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.mirrors[self.selected_index].rotate(4)
            elif k == pygame.K_r:
                self._reset()
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.win:
                    self.done = True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.Vector2(event.pos)
            pi = self._find_prism_at(pos)
            if pi is not None:
                self.dragging_prism  = pi
                self.dragging_mirror = None
                self.drag_offset     = self.prisms[pi]["center"] - pos
                return
            for i, m in enumerate(self.mirrors):
                if m.hit_test(pos):
                    self.selected_index  = i
                    self.dragging_mirror = i
                    self.dragging_prism  = None
                    self.last_mouse_pos  = pos
                    break

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_prism  = None
            self.dragging_mirror = None
            self.last_mouse_pos  = None

        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            pos = pygame.Vector2(event.pos)
            if self.dragging_prism is not None:
                nc = pos + self.drag_offset
                nc.x = max(40, min(self.width  - 40,  nc.x))
                nc.y = max(40, min(self.height - 180, nc.y))
                self.prisms[self.dragging_prism]["center"] = nc
            elif self.dragging_mirror is not None and self.last_mouse_pos is not None:
                m  = self.mirrors[self.dragging_mirror]
                v1 = self.last_mouse_pos - m.center
                v2 = pos - m.center
                if v1.length_squared() > 1e-6 and v2.length_squared() > 1e-6:
                    m.rotate(math.degrees(
                        math.atan2(v2.y, v2.x) - math.atan2(v1.y, v1.x)))
                self.last_mouse_pos = pos

    def handle_events(self, events):
        for e in events:
            self.handle_event(e)

    def _target_edges(self, rect):
        tl = pygame.Vector2(rect.topleft);  tr = pygame.Vector2(rect.topright)
        br = pygame.Vector2(rect.bottomright); bl = pygame.Vector2(rect.bottomleft)
        return [(tl,tr),(tr,br),(br,bl),(bl,tl)]

    def _find_closest_hit(self, origin, direction):
        """Find nearest obstacle.  Prisms are tested as solid bodies (entry only)."""
        best_t   = self.max_ray_dist
        best_hit = None

        for mirror in self.mirrors:
            a, b = mirror.endpoints()
            hit = _ray_segment_intersection(origin, direction, a, b)
            if hit:
                t, pt = hit
                if t < best_t:
                    best_t   = t
                    best_hit = {"kind": "mirror", "t": t, "point": pt,
                                "normal": mirror.outward_normal(direction)}

        for prism in self.prisms:
            entry = _ray_enter_prism(origin, direction, prism)
            if entry and entry["t"] < best_t:
                best_t   = entry["t"]
                best_hit = dict(entry, kind="prism")

        for kind, rect in (("red_target", self.red_target),
                            ("blue_target", self.blue_target)):
            for a, b in self._target_edges(rect):
                hit = _ray_segment_intersection(origin, direction, a, b)
                if hit:
                    t, pt = hit
                    if t < best_t:
                        best_t   = t
                        best_hit = {"kind": kind, "t": t, "point": pt}

        return best_hit

    def _trace_ray(self):
        direction = pygame.Vector2(
            math.cos(math.radians(self.sun_angle_deg)),
            math.sin(math.radians(self.sun_angle_deg)),
        ).normalize()

        segments = []
        hit_red  = False
        hit_blue = False

        queue = [(self.sun_origin, direction, "white", 0)]

        while queue:
            origin, direction, ray_type, split_depth = queue.pop(0)

            for _ in range(self.max_bounces):
                hit = self._find_closest_hit(origin, direction)
                if hit is None:
                    segments.append((origin, origin + direction*self.max_ray_dist, ray_type))
                    break

                segments.append((origin, hit["point"], ray_type))

                if hit["kind"] == "mirror":
                    direction = _reflect(direction, hit["normal"])
                    origin    = _nudge(hit["point"], direction)
                    continue

                if hit["kind"] == "prism":
                    if ray_type == "white" and split_depth < MAX_RAY_SPLITS:
                        for name, _col, n_glass in SPECTRUM:
                            result = _trace_through_prism(hit, direction, n_glass)
                            if result is None:
                                continue
                            exit_pt, exit_dir, internal = result
                            for seg_s, seg_e in internal:
                                segments.append((seg_s, seg_e, name))
                            queue.append((exit_pt, exit_dir, name, split_depth + 1))
                        break

                    else:
                        n_glass = 1.53
                        for sn, _, sng in SPECTRUM:
                            if sn == ray_type:
                                n_glass = sng
                                break
                        result = _trace_through_prism(hit, direction, n_glass)
                        if result is None:
                            break
                        exit_pt, exit_dir, internal = result
                        for seg_s, seg_e in internal:
                            segments.append((seg_s, seg_e, ray_type))
                        direction = exit_dir
                        origin    = exit_pt
                        continue

                if hit["kind"] == "red_target":
                    if ray_type == "red":
                        hit_red = True
                    break

                if hit["kind"] == "blue_target":
                    if ray_type == "blue":
                        hit_blue = True
                    break

                break

        return segments, hit_red, hit_blue

    def update(self, now_ms):
        dt = now_ms - self.last_update_ms
        self.last_update_ms = now_ms
        self.ray_segments, hit_red, hit_blue = self._trace_ray()
        self.red_charge  = max(0.0, min(100.0,
            self.red_charge  + (dt*0.06 if hit_red  else -dt*0.03)))
        self.blue_charge = max(0.0, min(100.0,
            self.blue_charge + (dt*0.06 if hit_blue else -dt*0.03)))
        self.win = self.red_charge >= 90.0 and self.blue_charge >= 90.0

    def _draw_scenery(self, screen):
        w, h = screen.get_size()
        pygame.draw.rect(screen, CAVE_WALL,  (0, 0, w, h))
        pygame.draw.rect(screen, CAVE_FLOOR, (0, h-140, w, 140))
        for x in range(0, w, 80):
            peak = 20 + int(12 * math.sin(x * 0.08))
            pygame.draw.polygon(screen, (22,22,28), [(x,0),(x+40,peak),(x+80,0)])
        for x in range(40, w, 200):
            pygame.draw.circle(screen, PLANT_GREEN, (x, h-150), 22)
            pygame.draw.circle(screen, (60,140,90),  (x+18, h-156), 16)

    def _draw_torch(self, screen):
        bx, by = int(self.sun_origin.x), int(self.sun_origin.y)
        pygame.draw.rect(screen, (70,60,50),
                         pygame.Rect(bx-8, by-6, 16, 12), border_radius=4)
        glow = pygame.Surface((220, 220), pygame.SRCALPHA)
        for r, a in [(90, 30), (65, 50), (40, 80)]:
            pygame.draw.circle(glow, (*TORCH_COLOR, a), (110, 110), r)
        screen.blit(glow, (bx-110, by-110))
        pygame.draw.circle(screen, TORCH_COLOR, (bx, by), 6)

    def _draw_beam_segment(self, surface, start, end, glow, core, w_start, w_end):
        d = end - start
        if d.length_squared() < 1e-6:
            return
        d = d.normalize()
        n = pygame.Vector2(-d.y, d.x)
        pygame.draw.polygon(surface, pygame.Color(*glow, 90),
            [start+n*w_start, start-n*w_start, end-n*w_end, end+n*w_end])
        pygame.draw.polygon(surface, pygame.Color(*core, 190),
            [start+n*w_start*0.45, start-n*w_start*0.45,
             end-n*w_end*0.45, end+n*w_end*0.45])

    def _draw_rays(self, screen):
        surf = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        for start, end, ray_type in self.ray_segments:
            glow, core = RAY_COLORS.get(ray_type, (RAY_GLOW, RAY_CORE))
            ds = start.distance_to(self.sun_origin)
            de = end.distance_to(self.sun_origin)
            self._draw_beam_segment(surf, start, end, glow, core,
                                    max(6.0, 22.0 - ds*0.03),
                                    max(4.0, 18.0 - de*0.03))
        screen.blit(surf, (0, 0))

    def _draw_prisms(self, screen):
        for p in self.prisms:
            pts = _prism_points(p["center"], p["size"], p.get("angle", 0.0))
            pygame.draw.polygon(screen, PRISM_COLOR, pts)
            pygame.draw.polygon(screen, PRISM_FRAME, pts, 2)

    def _draw_targets(self, screen):
        for rect, color, label in [
            (self.red_target,  PLANT_GREEN, "Crops"),
            (self.blue_target, PANEL_LIGHT, "Solar"),
        ]:
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, (100,100,100), rect, 2, border_radius=8)
            lbl = self.fonts["ui"].render(label, True, (255,255,255))
            screen.blit(lbl, lbl.get_rect(center=rect.center))

    def _draw_mirrors(self, screen):
        for i, m in enumerate(self.mirrors):
            a, b = m.endpoints()
            pygame.draw.line(screen, MIRROR_FRAME, a, b, 8)
            pygame.draw.line(screen, MIRROR_COLOR, a, b, 4)
            pygame.draw.circle(screen, MIRROR_FRAME, m.center, 10)
            pygame.draw.circle(screen, MIRROR_COLOR, m.center, 6)
            if i == self.selected_index:
                pygame.draw.circle(screen, ACCENT, m.center, 16, 2)

    def _draw_ui(self, screen):
        title = self.fonts["title"].render("Solar Lens Quest", True, UI_TEXT)
        bg    = pygame.Surface((title.get_width()+16, title.get_height()+8))
        bg.fill(UI_BG); bg.set_alpha(220)
        screen.blit(bg,    (16, 10))
        screen.blit(title, (24, 14))

        info    = self.fonts["small"].render(
            "Aim light: Red to Crops, Blue to Solar | Use mirrors", True, UI_TEXT)
        info_bg = pygame.Surface((info.get_width()+16, info.get_height()+8))
        info_bg.fill(UI_BG); info_bg.set_alpha(220)
        screen.blit(info_bg, (16, 50))
        screen.blit(info,    (24, 54))

        rx = self.width - 180
        screen.blit(self.fonts["ui"].render(
            f"Red: {self.red_charge:.0f}%", True, (255,80,80)), (rx, 24))
        screen.blit(self.fonts["ui"].render(
            f"Blue: {self.blue_charge:.0f}%", True, (80,150,255)), (rx, 80))

        for y, charge, fill_col in [
            (50,  self.red_charge,  ACCENT),
            (106, self.blue_charge, (100,180,255)),
        ]:
            bar = pygame.Rect(rx, y, 160, 16)
            pygame.draw.rect(screen, (248,244,226), bar, border_radius=8)
            fw = int(bar.width * charge / 100.0)
            if fw > 0:
                pygame.draw.rect(screen, fill_col,
                                 pygame.Rect(bar.left, bar.top, fw, bar.height),
                                 border_radius=8)

        if self.win:
            txt = self.fonts["ui"].render("Perfect balance! Press Enter", True, (0,200,0))
            screen.blit(txt, txt.get_rect(center=(self.width//2, 110)))

    def draw(self, screen):
        _draw_vertical_gradient(screen, SKY_TOP, SKY_BOTTOM)
        self._draw_scenery(screen)
        self._draw_torch(screen)
        self._draw_rays(screen)
        self._draw_targets(screen)
        self._draw_mirrors(screen)
        self._draw_prisms(screen)
        self._draw_ui(screen)

def create_solar_quest():
    return Solar()

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption("Solar Lens Quest")
    clock  = pygame.time.Clock()
    quest  = Solar()
    running = True
    while running:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
        quest.handle_events(events)
        quest.update(pygame.time.get_ticks())
        quest.draw(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()