from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

WINDOW_W = 1000
WINDOW_H = 800
fovY = 70

camera_angle = 315.0
camera_radius = 920.0
camera_height = 680.0
CAMERA_MIN_HEIGHT = 260.0
CAMERA_MAX_HEIGHT = 980.0
CAMERA_STEP_ANGLE = 5.0
CAMERA_STEP_HEIGHT = 25.0

STATE_MENU = "menu"
STATE_CUSTOMIZE = "customize"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAMEOVER = "gameover"
STATE_FAILED = "failed"
STATE_WIN = "win"
state = STATE_MENU

rabbit_colors = [
    (0.95, 0.95, 0.95),
    (1.00, 0.78, 0.82),
    (0.72, 0.90, 1.00),
    (1.00, 0.85, 0.50),
    (0.70, 1.00, 0.70),
]
selected_color_index = 0
saved_color_index = 0

DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
DIR_NAMES = ["N", "E", "S", "W"]
CARD_FORWARD = "FWD"
CARD_LEFT = "LEFT"
CARD_RIGHT = "RIGHT"
CARD_WAIT = "WAIT"
CARD_PLAY = "PLAY"
CARD_CLEAR = "CLEAR"
TOOL_CARDS = [CARD_FORWARD, CARD_LEFT, CARD_RIGHT, CARD_WAIT]

levels = []
current_level = 0
walkable_tiles = set()
traps = set()
carrots = []
portal_tile = (0, 0)
start_tile = (0, 0)
start_dir = 1
max_cards = 8
level_center = (0.0, 0.0)

rabbit_grid_x = 0
rabbit_grid_y = 0
rabbit_dir = 1
visited_tiles = set()
collected = set()
level_message = ""

selected_cards = []
executing_cards = False
current_card_step = 0
current_step_anim = 0.0
step_duration =30.0
move_start = (0.0, 0.0)
move_target = (0.0, 0.0)
current_action = ""
hop_height = 0.0
flash_tile = None
flash_amount = 0.0

click_regions = []

TILE_SIZE = 96.0

base_x = 180
y1 = 30
y2 = 110 

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(color[0], color[1], color[2])
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_rect(x1, y1, x2, y2, color, filled=True):
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS if filled else GL_LINE_LOOP)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()


def begin_2d():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_W, 0, WINDOW_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)


def end_2d():
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def register_click(name, rect, extra=None):
    click_regions.append((name, rect, extra))


def inside_rect(mx, my, rect):
    x1, y1, x2, y2 = rect
    return x1 <= mx <= x2 and y1 <= my <= y2


def normalize_angle_deg(a):
    while a < 0:
        a += 360
    while a >= 360:
        a -= 360
    return a


def deg_to_rad(deg):
    return deg * 3.141592653589793 / 180.0


def wrap_pi(x):
    pi = 3.141592653589793
    two_pi = 2.0 * pi
    while x > pi:
        x -= two_pi
    while x < -pi:
        x += two_pi
    return x


def sin_approx(x):
    x = wrap_pi(x)
    x2 = x * x
    x3 = x2 * x
    x5 = x3 * x2
    x7 = x5 * x2
    return x - x3 / 6.0 + x5 / 120.0 - x7 / 5040.0


def cos_approx(x):
    x = wrap_pi(x)
    x2 = x * x
    x4 = x2 * x2
    x6 = x4 * x2
    return 1.0 - x2 / 2.0 + x4 / 24.0 - x6 / 720.0


def set_perspective_camera():
    global camera_angle
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_W / float(WINDOW_H), 1.0, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    camera_angle = normalize_angle_deg(camera_angle)
    a = deg_to_rad(camera_angle)
    cx, cy = level_center
    cam_x = cx + camera_radius * cos_approx(a)
    cam_y = cy + camera_radius * sin_approx(a)
    gluLookAt(cam_x, cam_y, camera_height, cx, cy, 0, 0, 0, 1)


def grid_to_world(gx, gy):
    return gx * TILE_SIZE, gy * TILE_SIZE


def draw_cube_scaled(sx, sy, sz):
    glPushMatrix()
    glScalef(sx, sy, sz)
    glutSolidCube(1.0)
    glPopMatrix()


def draw_box_outline(sx, sy, sz):
    hx = sx / 2.0
    hy = sy / 2.0
    hz = sz / 2.0
    pts = [
        (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
        (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
    ]
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7),
    ]
    glColor3f(0, 0, 0)
    glLineWidth(2)
    glBegin(GL_LINES)
    for a, b in edges:
        glVertex3f(pts[a][0], pts[a][1], pts[a][2])
        glVertex3f(pts[b][0], pts[b][1], pts[b][2])
    glEnd()
    glLineWidth(1)


def draw_ground_plane():
    cx, cy = level_center
    glColor3f(0.38, 0.80, 0.78)
    glBegin(GL_QUADS)
    glVertex3f(cx - 1800, cy - 1800, -12)
    glVertex3f(cx + 1800, cy - 1800, -12)
    glVertex3f(cx + 1800, cy + 1800, -12)
    glVertex3f(cx - 1800, cy + 1800, -12)
    glEnd()


def draw_tile(gx, gy, color):
    wx, wy = grid_to_world(gx, gy)
    glPushMatrix()
    glTranslatef(wx, wy, 8)
    glColor3f(color[0], color[1], color[2])
    draw_cube_scaled(88, 88, 16)
    glColor3f(0.08, 0.08, 0.08)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-44, -44, 8.5)
    glVertex3f(44, -44, 8.5)
    glVertex3f(44, 44, 8.5)
    glVertex3f(-44, 44, 8.5)
    glEnd()
    glPopMatrix()


def draw_carrot(gx, gy):
    wx, wy = grid_to_world(gx, gy)
    glPushMatrix()
    glTranslatef(wx, wy, 16)

    q = gluNewQuadric()

    # Tall slim orange body pointing up
    glColor3f(1.0, 0.45, 0.05)
    gluCylinder(q, 6, 1, 48, 10, 4)   # slim, tall, pointy tip

    # Move to top
    glTranslatef(0, 0, 46)

    # Small teal/blue leaves like in picture
    glColor3f(0.20, 0.75, 0.85)        # teal-blue color!
    for angle in [0, 60, 120, 180, 240, 300]:
        glPushMatrix()
        glRotatef(angle, 0, 0, 1)
        glRotatef(35, 1, 0, 0)         # fan outward
        gluCylinder(q, 1.5, 0, 14, 5, 2)
        glPopMatrix()

    # Short upright center leaf
    glColor3f(0.15, 0.80, 0.90)
    gluCylinder(q, 1.5, 0, 18, 5, 2)

    glPopMatrix()


def draw_portal(gx, gy, active):
    wx, wy = grid_to_world(gx, gy)
    glPushMatrix()
    glTranslatef(wx, wy, 18)
    col = (0.78, 0.22, 1.0) if active else (0.35, 0.24, 0.50)
    glColor3f(col[0], col[1], col[2])
    glBegin(GL_QUAD_STRIP)
    segments = 28
    for i in range(segments + 1):
        ang = deg_to_rad((360.0 / segments) * i)
        c = cos_approx(ang)
        s = sin_approx(ang)
        glVertex3f(c * 18, s * 18, 0)
        glVertex3f(c * 28, s * 28, 0)
    glEnd()
    glColor3f(0.9, 0.85, 1.0 if active else 0.7)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        ang = deg_to_rad((360.0 / segments) * i)
        glVertex3f(cos_approx(ang) * 23, sin_approx(ang) * 23, 0.5)
    glEnd()
    glPopMatrix()


def draw_trap(gx, gy):
    wx, wy = grid_to_world(gx, gy)
    glPushMatrix()
    glTranslatef(wx, wy, 9)
    glColor3f(0.82, 0.18, 0.18)
    for i in range(6):
        glPushMatrix()
        glRotatef(i * 60, 0, 0, 1)
        glTranslatef(16, 0, 6)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 0, 5, 18, 8, 2)
        glPopMatrix()
    glPopMatrix()


def draw_rabbit(world_x, world_y, direction, color, hop):
    angle = [0, -90, 180, 90][direction]
    glPushMatrix()
    glTranslatef(world_x, world_y, 18 + hop)
    glRotatef(angle, 0, 0, 1)

    # --- BODY — big white box ---
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(0, 0, 18)
    draw_cube_scaled(42, 30, 36)
    draw_box_outline(42, 30, 36)
    glPopMatrix()

    # --- HEAD — white box ---
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(0, 16, 46)
    draw_cube_scaled(36, 30, 30)
    draw_box_outline(36, 30, 30)
    glPopMatrix()

    # --- EARS — tall white ---
    for ex in (-10, 10):
        glColor3f(1.0, 1.0, 1.0)
        glPushMatrix()
        glTranslatef(ex, 20, 72)
        draw_cube_scaled(10, 8, 32)
        draw_box_outline(10, 8, 32)
        glPopMatrix()

        # Pink inside ear
        glColor3f(1.0, 0.55, 0.75)
        glPushMatrix()
        glTranslatef(ex, 21, 72)
        draw_cube_scaled(5, 4, 24)
        glPopMatrix()

    # --- EYES — dark navy blue circles (boxes) ---
    glColor3f(0.10, 0.20, 0.55)
    for ex in (-10, 10):
        glPushMatrix()
        glTranslatef(ex, 30, 48)
        draw_cube_scaled(9, 5, 9)
        glPopMatrix()

    # --- NOSE — pink triangle box ---
    glColor3f(0.95, 0.40, 0.60)
    glPushMatrix()
    glTranslatef(0, 30, 40)
    draw_cube_scaled(7, 4, 5)
    glPopMatrix()

    # --- WHISKERS — dark lines left and right ---
    glColor3f(0.05, 0.05, 0.05)
    glLineWidth(2)
    glBegin(GL_LINES)
    # left whiskers
    glVertex3f(-18, 29, 41)
    glVertex3f(-4,  29, 41)
    glVertex3f(-18, 29, 38)
    glVertex3f(-4,  29, 38)
    # right whiskers
    glVertex3f(4,  29, 41)
    glVertex3f(18, 29, 41)
    glVertex3f(4,  29, 38)
    glVertex3f(18, 29, 38)
    glEnd()
    glLineWidth(1)

    # --- LEGS — teal/blue boxes at bottom ---
    glColor3f(0.25, 0.65, 0.80)
    for lx in (-11, 11):
        glPushMatrix()
        glTranslatef(lx, 0, 6)
        draw_cube_scaled(14, 18, 12)
        draw_box_outline(14, 18, 12)
        glPopMatrix()

    glPopMatrix()


def make_level(tiles, start, start_facing, carrots_list, portal, trap_list, max_cards_level):
    return {
        "tiles": set(tiles),
        "start": start,
        "start_dir": start_facing,
        "carrots": carrots_list[:],
        "portal": portal,
        "traps": set(trap_list),
        "max_cards": max_cards_level,
    }


def build_levels():
    global levels
    levels = [
        make_level(
            [
                (0, 0), (1, 0), (2, 0),
                (0, 1),         (2, 1),
                (0, 2), (1, 2), (2, 2), (3, 2),
                                (3, 3), (4, 3),
            ],
            (0, 0),
            1,
            [(2, 0), (2, 2), (4, 3)],
            (3, 3),
            [],
            10,
        ),
        make_level(
            [
                (0, 0), (1, 0), (2, 0),
                        (1, 1),         (3, 1),
                (0, 2), (1, 2), (2, 2), (3, 2),
                (0, 3),                 (3, 3),
                (0, 4), (1, 4), (2, 4), (3, 4), (4, 4),
                                            (4, 5),
            ],
            (0, 0),
            1,
            [(2, 0), (3, 2), (1, 4), (4, 5)],
            (4, 4),
            [(1, 1), (0, 3)],
            18,
        ),
        make_level(
            [
                (0, 0), (1, 0), (2, 0),
                        (1, 1),         (3, 1),
                (0, 2), (1, 2), (2, 2), (3, 2), (4, 2),
                (0, 3),                 (3, 3),         (5, 3),
                (0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 4),
                                        (3, 5),         (5, 5),
                                        (3, 6), (4, 6), (5, 6),
            ],
            (0, 0),
            1,
            [(2, 0), (4, 2), (0, 4), (5, 4), (5, 6)],
            (4, 6),
            [(1, 1), (3, 3), (5, 5)],
            24,
        ),
    ]


def recompute_level_center():
    global level_center
    if not walkable_tiles:
        level_center = (0.0, 0.0)
        return
    min_x = min(t[0] for t in walkable_tiles)
    max_x = max(t[0] for t in walkable_tiles)
    min_y = min(t[1] for t in walkable_tiles)
    max_y = max(t[1] for t in walkable_tiles)
    level_center = ((min_x + max_x) * TILE_SIZE / 2.0, (min_y + max_y) * TILE_SIZE / 2.0)


def current_level_data():
    return levels[current_level]


def reset_level(level_idx):
    global current_level, walkable_tiles, traps, carrots, portal_tile, start_tile, start_dir, max_cards
    global rabbit_grid_x, rabbit_grid_y, rabbit_dir, visited_tiles, collected, selected_cards
    global executing_cards, current_card_step, current_step_anim, move_start, move_target, current_action
    global hop_height, flash_tile, flash_amount, level_message, state

    current_level = level_idx
    lvl = levels[level_idx]
    walkable_tiles = set(lvl["tiles"])
    traps = set(lvl["traps"])
    carrots = lvl["carrots"][:]
    portal_tile = lvl["portal"]
    start_tile = lvl["start"]
    start_dir = lvl["start_dir"]
    max_cards = lvl["max_cards"]
    recompute_level_center()

    rabbit_grid_x, rabbit_grid_y = start_tile
    rabbit_dir = start_dir
    visited_tiles = {start_tile}
    collected = set()
    selected_cards = []
    executing_cards = False
    current_card_step = 0
    current_step_anim = 0.0
    move_start = (float(rabbit_grid_x), float(rabbit_grid_y))
    move_target = move_start
    current_action = ""
    hop_height = 0.0
    flash_tile = start_tile
    flash_amount = 1.0
    level_message = "Collect all carrots, then enter the portal"
    state = STATE_PLAYING
    collect_carrot_if_here()


def restart_current_level():
    reset_level(current_level)


def all_carrots_collected():
    return len(collected) == len(carrots)


def portal_active():
    return all_carrots_collected()


def collect_carrot_if_here():
    global level_message
    pos = (rabbit_grid_x, rabbit_grid_y)
    for c in carrots:
        if c == pos and c not in collected:
            collected.add(c)
            level_message = "Carrot collected"
            return


def check_trap_or_finish():
    global state, level_message
    pos = (rabbit_grid_x, rabbit_grid_y)
    if pos in traps:
        state = STATE_GAMEOVER
        level_message = "Stepped on a trap"
        return
    if pos == portal_tile and portal_active():
        if current_level < len(levels) - 1:
            reset_level(current_level + 1)
            level_message = "Level complete"
        else:
            state = STATE_WIN
            level_message = "All levels complete"


def execute_card_action(card):
    global rabbit_dir, rabbit_grid_x, rabbit_grid_y, move_start, move_target, flash_tile, flash_amount, level_message
    pos = (rabbit_grid_x, rabbit_grid_y)

    if card == CARD_LEFT:
        rabbit_dir = (rabbit_dir - 1) % 4
        move_start = (float(rabbit_grid_x), float(rabbit_grid_y))
        move_target = move_start
        flash_tile = pos
        flash_amount = 1.0
        level_message = "Turned left"
        return

    if card == CARD_RIGHT:
        rabbit_dir = (rabbit_dir + 1) % 4
        move_start = (float(rabbit_grid_x), float(rabbit_grid_y))
        move_target = move_start
        flash_tile = pos
        flash_amount = 1.0
        level_message = "Turned right"
        return

    if card == CARD_WAIT:
        move_start = (float(rabbit_grid_x), float(rabbit_grid_y))
        move_target = move_start
        flash_tile = pos
        flash_amount = 1.0
        level_message = "Wait"
        return

    if card == CARD_FORWARD:
        dx, dy = DIRS[rabbit_dir]
        nx, ny = rabbit_grid_x + dx, rabbit_grid_y + dy
        move_start = (float(rabbit_grid_x), float(rabbit_grid_y))
        if (nx, ny) in walkable_tiles:
            rabbit_grid_x, rabbit_grid_y = nx, ny
            move_target = (float(nx), float(ny))
            visited_tiles.add((nx, ny))
            flash_tile = (nx, ny)
            flash_amount = 1.0
            level_message = "Hop"
        else:
            move_target = move_start
            flash_tile = pos
            flash_amount = 1.0
            level_message = "Blocked"


def simulate_sequence(sequence):
    x, y = start_tile
    d = start_dir
    got = set()
    for card in sequence:
        if card == CARD_LEFT:
            d = (d - 1) % 4
        elif card == CARD_RIGHT:
            d = (d + 1) % 4
        elif card == CARD_FORWARD:
            dx, dy = DIRS[d]
            nx, ny = x + dx, y + dy
            if (nx, ny) not in walkable_tiles:
                return False
            x, y = nx, ny
            if (x, y) in traps:
                return False
            if (x, y) in carrots:
                got.add((x, y))
        if (x, y) in carrots:
            got.add((x, y))
    return (x, y) == portal_tile and len(got) == len(carrots)


def solve_level_cards(level_idx):
    lvl = levels[level_idx]
    tiles = lvl["tiles"]
    local_traps = lvl["traps"]
    local_carrots = lvl["carrots"][:]
    local_portal = lvl["portal"]
    card_limit = lvl["max_cards"]
    start = lvl["start"]
    sdir = lvl["start_dir"]

    target_mask = 0
    for i in range(len(local_carrots)):
        target_mask |= (1 << i)

    queue = [((start[0], start[1], sdir, 0), [])]
    seen = {(start[0], start[1], sdir, 0)}
    head = 0

    while head < len(queue):
        state_node, seq = queue[head]
        head += 1
        x, y, d, mask = state_node

        if len(seq) > card_limit:
            continue

        if (x, y) == local_portal and mask == target_mask:
            return seq

        for card in (CARD_FORWARD, CARD_LEFT, CARD_RIGHT):
            nx, ny, nd, nmask = x, y, d, mask
            if card == CARD_LEFT:
                nd = (d - 1) % 4
            elif card == CARD_RIGHT:
                nd = (d + 1) % 4
            else:
                dx, dy = DIRS[d]
                nx, ny = x + dx, y + dy
                if (nx, ny) not in tiles or (nx, ny) in local_traps:
                    continue
            for i, c in enumerate(local_carrots):
                if c == (nx, ny):
                    nmask |= (1 << i)
            node = (nx, ny, nd, nmask)
            if node not in seen:
                seen.add(node)
                queue.append((node, seq + [card]))

    return []


def draw_button(rect, text, fill, text_color=(1, 1, 1), border=(1, 1, 1), extra=None):
    x1, y1, x2, y2 = rect
    draw_rect(x1, y1, x2, y2, fill, True)
    draw_rect(x1, y1, x2, y2, border, False)
    draw_text((x1 + x2) / 2 - len(text) * 4, (y1 + y2) / 2 - 5, text, color=text_color)
    register_click(text, rect, extra)


def draw_card_slot(rect, text, fill, extra=None):
    x1, y1, x2, y2 = rect
    draw_rect(x1, y1, x2, y2, fill, True)
    draw_rect(x1, y1, x2, y2, (1, 1, 1), False)
    draw_text(x1 + 12, y1 + 20, text, color=(0.06, 0.06, 0.06))
    register_click(text, rect, extra)



def build_menu_ui():
    begin_2d()
    draw_text(330, 700, "Rabbit Coding Adventure", GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.95, 0.35))
    draw_text(260, 650, "Inspired by Celebrating 50 years of Kids Coding Doodle", color=(0.9, 0.9, 1))
    draw_button((390, 450, 610, 515), "P", (0.25, 0.65, 0.35))
    draw_text(445, 420, "Play", color=(1, 1, 1))
    draw_button((390, 320, 610, 385), "C", (0.30, 0.40, 0.85))
    draw_text(410, 290, "Customize Rabbit", color=(1, 1, 1))
    draw_text(210, 170, "Arrows: rotate/move camera height   P pause/play   R restart   C cheat", color=(0.84, 0.84, 0.84))
    end_2d()


def build_customize_ui():
    begin_2d()
    draw_text(385, 700, "Customize Rabbit", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.92, 0.45))
    draw_text(305, 650, "Click a color. It will stay selected when you play.", color=(1, 1, 1))
    base_x = 240
    for i, col in enumerate(rabbit_colors):
        rect = (base_x + i * 110, 430, base_x + i * 110 + 70, 500)
        draw_rect(rect[0], rect[1], rect[2], rect[3], col, True)
        draw_rect(rect[0] - 3, rect[1] - 3, rect[2] + 3, rect[3] + 3, (1, 1, 0.2) if i == selected_color_index else (1, 1, 1), False)
        register_click("COLOR", rect, i)
    draw_button((290, 200, 460, 260), "BACK", (0.48, 0.24, 0.24))
    draw_button((540, 200, 710, 260), "P", (0.20, 0.65, 0.30))
    draw_text(585, 170, "Play", color=(1, 1, 1))
    end_2d()


def build_game_ui():
    begin_2d()
    draw_rect(0, 0, WINDOW_W, 220, (0.10, 0.12, 0.18), True)
    draw_text(20, 770, "Level %d/3" % (current_level + 1), color=(1, 1, 0.5))
    draw_text(20, 740, "Facing: %s" % DIR_NAMES[rabbit_dir], color=(1, 1, 1))
    draw_text(20, 710, "Carrots: %d/%d" % (len(collected), len(carrots)), color=(1, 1, 1))
    draw_text(20, 680, level_message, color=(0.82, 1, 0.82))
    draw_text(20, 650, "Cards limit: %d" % max_cards, color=(1, 1, 1))

    if state == STATE_PAUSED:
        draw_text(430, 720, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.7, 0.4))
    elif state == STATE_GAMEOVER:
        draw_text(395, 720, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.35, 0.35))
    elif state == STATE_WIN:
        draw_text(370, 720, "YOU FINISHED ALL LEVELS", GLUT_BITMAP_TIMES_ROMAN_24, (0.65, 1, 0.5))

    draw_text(320, 200, "Selected Card Sequence", color=(1, 1, 1))
    sx = 230
    for i in range(max_cards):
        rect = (sx + i * 65, 145, sx + i * 65 + 55, 185)
        slot_colors = {
            CARD_FORWARD: (0.20, 0.72, 0.38),
            CARD_LEFT:    (0.18, 0.52, 0.90),
            CARD_RIGHT:   (0.95, 0.55, 0.10),
            CARD_WAIT:    (0.70, 0.30, 0.85),
        }
        if i < len(selected_cards):
            sc = slot_colors.get(selected_cards[i], (0.95, 0.85, 0.45))
            draw_card_slot(rect, selected_cards[i], sc, i)
        else:
            draw_card_slot(rect, "-", (0.28, 0.28, 0.32), None)
    draw_text(295, 115, "Click cards below to add. Click selected cards to remove.", color=(0.95, 0.95, 0.95))
    base_x = 220
    y1 = 45
    y2 = 95
    colors = {
        CARD_FORWARD: (0.55, 0.95, 0.55),
        CARD_LEFT: (0.60, 0.85, 1.0),
        CARD_RIGHT: (1.0, 0.82, 0.50),
        CARD_WAIT: (0.85, 0.75, 0.98),
    }
    for i, c in enumerate(TOOL_CARDS):
        rect = (base_x + i * 155, y1, base_x + i * 155 + 130, y2)
        draw_card_slot(rect, c, colors[c], c)

    draw_button((790, 135, 930, 190), CARD_PLAY, (0.20, 0.65, 0.30))
    draw_button((790, 60, 930, 115), CARD_CLEAR, (0.70, 0.25, 0.25))
    if executing_cards and current_card_step < len(selected_cards):
        hi_rect = (sx + current_card_step * 65 - 3, 142,
                sx + current_card_step * 65 + 58, 188)
        draw_rect(hi_rect[0], hi_rect[1], hi_rect[2], hi_rect[3], (1, 1, 0.2), False)
    end_2d()


def handle_ui_click(mx, my):
    global state, selected_color_index, saved_color_index, selected_cards, level_message
    for name, rect, extra in click_regions:
        if not inside_rect(mx, my, rect):
            continue

        if state == STATE_MENU:
            if name == "P":
                saved_color_index = selected_color_index
                reset_level(0)
                return
            if name == "C":
                state = STATE_CUSTOMIZE
                return

        elif state == STATE_CUSTOMIZE:
            if name == "COLOR":
                selected_color_index = extra
                saved_color_index = extra
                return
            if name == "BACK":
                state = STATE_MENU
                return
            if name == "P":
                saved_color_index = selected_color_index
                reset_level(0)
                return

        elif state == STATE_PLAYING:
            if name in TOOL_CARDS and not executing_cards:
                if len(selected_cards) < max_cards:
                    selected_cards.append(name)
                    level_message = "Card added"
                return
            if name == CARD_PLAY and not executing_cards and selected_cards:
                start_card_execution()
                return
            if name == CARD_CLEAR and not executing_cards:
                selected_cards = []
                level_message = "Sequence cleared"
                return
            if extra is not None and isinstance(extra, int) and name in TOOL_CARDS and not executing_cards:
                if 0 <= extra < len(selected_cards):
                    selected_cards.pop(extra)
                    level_message = "Card removed"
                return


def start_card_execution():
    global executing_cards, current_card_step, current_step_anim, level_message
    if not selected_cards:
        return
    executing_cards = True
    current_card_step = 0
    current_step_anim = 0.0
    level_message = "Running cards"


def keyboardListener(key, x, y):
    global state, selected_cards
    if key == b'p' or key == b'P':
        if state == STATE_MENU:
            reset_level(0)
        elif state == STATE_CUSTOMIZE:
            reset_level(0)
        elif state == STATE_PLAYING:
            state = STATE_PAUSED
        elif state == STATE_PAUSED:
            state = STATE_PLAYING
        elif state == STATE_GAMEOVER or state == STATE_FAILED:
            restart_current_level()
        elif state == STATE_WIN:
            state = STATE_MENU
    elif key == b'r' or key == b'R':
        if state in (STATE_PLAYING, STATE_PAUSED, STATE_GAMEOVER, STATE_FAILED):
            restart_current_level()
        elif state == STATE_WIN:
            reset_level(0)
    elif key == b'c' or key == b'C':
        if state == STATE_MENU:
            state = STATE_CUSTOMIZE
        elif state in (STATE_PLAYING, STATE_PAUSED) and not executing_cards:
            selected_cards = solve_level_cards(current_level)
            if selected_cards:
                if state == STATE_PAUSED:
                    state = STATE_PLAYING
                start_card_execution()
            else:
                level_message = "No valid solve found"
    glutPostRedisplay()


def specialKeyListener(key, x, y):
    global camera_angle, camera_height
    if key == GLUT_KEY_LEFT:
        camera_angle += CAMERA_STEP_ANGLE
    elif key == GLUT_KEY_RIGHT:
        camera_angle -= CAMERA_STEP_ANGLE
    elif key == GLUT_KEY_UP:
        camera_height += CAMERA_STEP_HEIGHT
        if camera_height > CAMERA_MAX_HEIGHT:
            camera_height = CAMERA_MAX_HEIGHT
    elif key == GLUT_KEY_DOWN:
        camera_height -= CAMERA_STEP_HEIGHT
        if camera_height < CAMERA_MIN_HEIGHT:
            camera_height = CAMERA_MIN_HEIGHT
    glutPostRedisplay()


def mouseListener(button, state_btn, x, y):
    if button == GLUT_LEFT_BUTTON and state_btn == GLUT_DOWN:
        handle_ui_click(x, WINDOW_H - y)
    glutPostRedisplay()


def update_execution():
    global executing_cards, current_card_step, current_step_anim, current_action, hop_height, state, level_message

    if not executing_cards or state != STATE_PLAYING:
        return

    if current_card_step >= len(selected_cards):
        executing_cards = False
        current_action = ""
        hop_height = 0.0
        if state == STATE_PLAYING:
            if (rabbit_grid_x, rabbit_grid_y) == portal_tile and portal_active():
                check_trap_or_finish()
            elif state == STATE_PLAYING:
                state = STATE_FAILED
                level_message = "FAILED"
        return

    if current_step_anim == 0.0:
        current_action = selected_cards[current_card_step]
        execute_card_action(current_action)

    current_step_anim += 1.0
    t = current_step_anim / step_duration
    if t > 1.0:
        t = 1.0
    wave = 1.0 - (2.0 * t - 1.0) * (2.0 * t - 1.0)
    hop_height = (26.0 if current_action == CARD_FORWARD else 10.0) * wave

    if current_step_anim >= step_duration:
        current_step_anim = 0.0
        hop_height = 0.0
        collect_carrot_if_here()
        check_trap_or_finish()
        if state == STATE_PLAYING:
            current_card_step += 1
        else:
            executing_cards = False


def update_flash():
    global flash_amount
    if flash_amount > 0:
        flash_amount -= 0.03
        if flash_amount < 0:
            flash_amount = 0.0


def idle():
    update_execution()
    update_flash()
    glutPostRedisplay()


def draw_level_scene():
    draw_ground_plane()
    for gx, gy in walkable_tiles:
        base = (0.29, 0.78, 0.65) if (gx + gy) % 2 == 0 else (0.22, 0.68, 0.58)
        if (gx, gy) in visited_tiles:
            base = (0.75, 0.65, 0.85) 
        if flash_tile == (gx, gy) and flash_amount > 0:
            boost = flash_amount * 0.3
            base = (min(base[0] + boost, 1), min(base[1] + boost, 1), min(base[2] + boost, 1))
        draw_tile(gx, gy, base)

    for tx, ty in traps:
        draw_trap(tx, ty)

    for c in carrots:
        if c not in collected:
            draw_carrot(c[0], c[1])

    draw_portal(portal_tile[0], portal_tile[1], portal_active())

    if executing_cards and current_action == CARD_FORWARD and current_step_anim > 0:
        t = current_step_anim / step_duration
        if t > 1.0:
            t = 1.0
        draw_x = move_start[0] + (move_target[0] - move_start[0]) * t
        draw_y = move_start[1] + (move_target[1] - move_start[1]) * t
    else:
        draw_x = float(rabbit_grid_x)
        draw_y = float(rabbit_grid_y)

    wx, wy = grid_to_world(draw_x, draw_y)
    draw_rabbit(wx, wy, rabbit_dir, rabbit_colors[saved_color_index], hop_height)


def draw_customize_preview():
    set_perspective_camera()
    draw_ground_plane()
    draw_tile(0, 0, (0.46, 0.62, 0.42))
    draw_rabbit(0, 0, 0, rabbit_colors[selected_color_index], 0)


def show_failed_overlay():
    begin_2d()
    draw_text(430, 430, "FAILED", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.25, 0.25))
    draw_text(320, 380, "Sequence did not finish the level", color=(1, 1, 1))
    draw_text(350, 340, "Press R to restart", color=(1, 1, 0.7))
    end_2d()


def showScreen():
    global click_regions
    click_regions = []
    glClearColor(0.45, 0.88, 0.85, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    if state == STATE_MENU:
        set_perspective_camera()
        draw_ground_plane()
        draw_tile(-1, 0, (0.45, 0.60, 0.40))
        draw_tile(0, 0, (0.36, 0.52, 0.34))
        draw_tile(1, 0, (0.45, 0.60, 0.40))
        draw_rabbit(0, 0, 0, rabbit_colors[saved_color_index], 0)
        build_menu_ui()
    elif state == STATE_CUSTOMIZE:
        draw_customize_preview()
        build_customize_ui()
    else:
        set_perspective_camera()
        draw_level_scene()
        if state == STATE_FAILED:
            show_failed_overlay()
        else:
            build_game_ui()

    glutSwapBuffers()


def main():
    build_levels()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Rabbit Coding Adventure")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()
