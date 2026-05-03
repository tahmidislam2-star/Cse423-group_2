from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

WINDOW_W = 1000
WINDOW_H = 800
fovY = 70

camera_angle = 315.0
camera_radius = 920.0
camera_height =420
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
    (1.00, 0.85, 0.50),
    (0.4, 0.4, 0.4),
    (0.15, 0.15, 0.15),
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

fox_grid_x = 0
fox_grid_y = 0
fox_dir = 1
fox_active = False
fox_present = False

selected_cards = []
executing_cards = False
current_card_step = 0
current_step_anim = 0.0
step_duration =60.0
move_start = (0.0, 0.0)
move_target = (0.0, 0.0)
current_action = ""
hop_height = 0.0
flash_tile = None
flash_amount = 0.0
carrot_bob_time = 0
click_regions = []
portal_angle = 0.0  

TILE_SIZE = 96.0

base_x = 180
y1 = 30
y2 = 110 
card_view_offset = 0
MAX_VISIBLE_CARDS = 10

clouds = [
    {"x": -180, "y": 260, "z": 180, "base_z": 180, "phase": 0},
    {"x": -30, "y": 260, "z": 180, "base_z": 180, "phase": 2.4},
    {"x": -340, "y": 200, "z": 210, "base_z": 210, "phase": 3.6},
]
cloud_time = 0.0

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


def draw_tile(gx, gy, color, height=1):
    wx, wy = grid_to_world(gx, gy)
    
    # Each cube is 16 units tall, stacked `height` times
    cube_h = 16
    total_h = cube_h * height
    half = 44  # half of tile width (88/2)

    # --- TOP FACE ---
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    glVertex3f(wx - half, wy - half, total_h)
    glVertex3f(wx + half, wy - half, total_h)
    glVertex3f(wx + half, wy + half, total_h)
    glVertex3f(wx - half, wy + half, total_h)
    glEnd()

    # --- LEFT FACE (front-left side, darker) ---
    glColor3f(color[0] * 0.60, color[1] * 0.60, color[2] * 0.60)
    glBegin(GL_QUADS)
    glVertex3f(wx - half, wy - half, 0)
    glVertex3f(wx + half, wy - half, 0)
    glVertex3f(wx + half, wy - half, total_h)
    glVertex3f(wx - half, wy - half, total_h)
    glEnd()

    # --- RIGHT FACE (front-right side, medium shade) ---
    glColor3f(color[0] * 0.75, color[1] * 0.75, color[2] * 0.75)
    glBegin(GL_QUADS)
    glVertex3f(wx + half, wy - half, 0)
    glVertex3f(wx + half, wy + half, 0)
    glVertex3f(wx + half, wy + half, total_h)
    glVertex3f(wx + half, wy - half, total_h)
    glEnd()

    # --- TOP FACE OUTLINE ---
    glColor3f(0.08, 0.08, 0.08)
    glBegin(GL_LINE_LOOP)
    glVertex3f(wx - half, wy - half, total_h + 0.5)
    glVertex3f(wx + half, wy - half, total_h + 0.5)
    glVertex3f(wx + half, wy + half, total_h + 0.5)
    glVertex3f(wx - half, wy + half, total_h + 0.5)
    glEnd()

    # --- VERTICAL EDGE OUTLINES (corners of the cube) ---
    glColor3f(0.08, 0.08, 0.08)
    glLineWidth(1)
    glBegin(GL_LINES)
    # Front-left vertical edge
    glVertex3f(wx - half, wy - half, 0)
    glVertex3f(wx - half, wy - half, total_h)
    # Front-right vertical edge
    glVertex3f(wx + half, wy - half, 0)
    glVertex3f(wx + half, wy - half, total_h)
    # Back-right vertical edge
    glVertex3f(wx + half, wy + half, 0)
    glVertex3f(wx + half, wy + half, total_h)
    # Bottom edge of left face
    glVertex3f(wx - half, wy - half, 0)
    glVertex3f(wx + half, wy - half, 0)
    # Bottom edge of right face
    glVertex3f(wx + half, wy - half, 0)
    glVertex3f(wx + half, wy + half, 0)
    glEnd()

def get_tile_z(gx, gy):
    """Returns the world Z of the top surface of a tile."""
    return current_level_data().get("heights", {}).get((gx, gy), 1) * 16

def draw_carrot(gx, gy):
    wx, wy = grid_to_world(gx, gy)
    z = get_tile_z(gx, gy)
    phase = (gx * 2.3 + gy * 1.7)
    bob = sin_approx(carrot_bob_time + phase) * 5.0

    glPushMatrix()
    glTranslatef(wx, wy, z + 4 + bob)

    #orange bod
    glColor3f(0.85, 0.35, 0.04)
    gluCylinder(gluNewQuadric(), 1.5, 10, 50, 10, 6)

    #leaf
    glTranslatef(0, 0, 50)
    leaf_angles = [0, 120, 240]
    for angle in leaf_angles:
        glPushMatrix()
        glRotatef(angle, 0, 0, 1)
        glRotatef(40, 1, 0, 0)
        glColor3f(0.25, 0.75, 0.10)
        gluCylinder(gluNewQuadric(), 2, 0, 22, 6, 2)
        glPopMatrix()

    glPopMatrix()

def draw_portal(gx, gy, active):
    wx, wy = grid_to_world(gx, gy)
    z = get_tile_z(gx, gy)

    glPushMatrix()
    glTranslatef(wx, wy, z + 1)

    # colors
    if active:
        inner  = (0.40, 0.85, 1.00)
        mid    = (0.10, 0.50, 1.00)
        outer  = (0.05, 0.20, 0.80)
        beam   = (0.20, 0.60, 1.00)
        glow   = (0.00, 0.70, 1.00)
    else:
        inner  = (0.30, 0.30, 0.55)
        mid    = (0.18, 0.18, 0.42)
        outer  = (0.10, 0.10, 0.30)
        beam   = (0.20, 0.20, 0.45)
        glow   = (0.15, 0.15, 0.40)

    segments = 48

    # ── OUTER GLOW RING (widest, darkest) ──
    glColor3f(outer[0], outer[1], outer[2])
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        ang = deg_to_rad(360.0 / segments * i)
        c, s = cos_approx(ang), sin_approx(ang)
        glVertex3f(c * 26, s * 26, 0)
        glVertex3f(c * 40, s * 40, 0)
    glEnd()

    # ── MID RING ──
    glColor3f(mid[0], mid[1], mid[2])
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        ang = deg_to_rad(360.0 / segments * i)
        c, s = cos_approx(ang), sin_approx(ang)
        glVertex3f(c * 22, s * 22, 0)
        glVertex3f(c * 36, s * 36, 0)
    glEnd()

    # ── INNER BRIGHT RING ──
    glColor3f(inner[0], inner[1], inner[2])
    glBegin(GL_QUAD_STRIP)
    for i in range(segments + 1):
        ang = deg_to_rad(360.0 / segments * i)
        c, s = cos_approx(ang), sin_approx(ang)
        glVertex3f(c * 10, s * 10, 0)
        glVertex3f(c * 22, s * 22, 0)
    glEnd()

    # ── BRIGHT CENTER DISC ──
    glColor3f(glow[0], glow[1], glow[2])
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(segments + 1):
        ang = deg_to_rad(360.0 / segments * i)
        glVertex3f(cos_approx(ang) * 10, sin_approx(ang) * 10, 0)
    glEnd()

    # ── SPINNING DASHED RING (rotates with portal_angle) ──
    glColor3f(inner[0], inner[1], inner[2])
    glLineWidth(2)
    glBegin(GL_LINES)
    dash_count = 24
    for i in range(dash_count):
        ang1 = deg_to_rad((360.0 / dash_count * i) + portal_angle)
        ang2 = deg_to_rad((360.0 / dash_count * i) + portal_angle + 6)
        glVertex3f(cos_approx(ang1) * 30, sin_approx(ang1) * 30, 1)
        glVertex3f(cos_approx(ang2) * 30, sin_approx(ang2) * 30, 1)
    glEnd()

    # ── COUNTER-SPINNING INNER DASHES ──
    glColor3f(glow[0], glow[1], glow[2])
    glBegin(GL_LINES)
    for i in range(dash_count):
        ang1 = deg_to_rad((360.0 / dash_count * i) - portal_angle * 1.5)
        ang2 = deg_to_rad((360.0 / dash_count * i) - portal_angle * 1.5 + 8)
        glVertex3f(cos_approx(ang1) * 18, sin_approx(ang1) * 18, 1)
        glVertex3f(cos_approx(ang2) * 18, sin_approx(ang2) * 18, 1)
    glEnd()
    glLineWidth(1)

    # ── LIGHT BEAMS shooting upward ──
    if active:
        beam_count = 8
        for i in range(beam_count):
            ang = deg_to_rad((360.0 / beam_count * i) + portal_angle * 0.5)
            bx = cos_approx(ang) * 20
            by = sin_approx(ang) * 20
            # fade from bright base to transparent tip
            glBegin(GL_TRIANGLES)
            glColor3f(beam[0], beam[1], beam[2])
            glVertex3f(bx - cos_approx(ang + deg_to_rad(90)) * 4,
                       by - sin_approx(ang + deg_to_rad(90)) * 4, 0)
            glVertex3f(bx + cos_approx(ang + deg_to_rad(90)) * 4,
                       by + sin_approx(ang + deg_to_rad(90)) * 4, 0)
            glColor3f(beam[0] * 0.2, beam[1] * 0.2, beam[2] * 0.2)
            glVertex3f(bx * 0.4, by * 0.4, 120)   # beam tip height
            glEnd()

    # ── OUTER GLOW LINE ──
    glColor3f(mid[0], mid[1], mid[2])
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        ang = deg_to_rad(360.0 / segments * i)
        glVertex3f(cos_approx(ang) * 44, sin_approx(ang) * 44, 0.5)
    glEnd()
    glLineWidth(1)

    glPopMatrix()

def draw_trap(gx, gy):
    wx, wy = grid_to_world(gx, gy)
    z = get_tile_z(gx, gy)
    glPushMatrix()
    glTranslatef(wx, wy, z)

    q = gluNewQuadric()

    # 3 pointy spikes arranged in a triangle
    spike_positions = [
        ( 0,   12),   # front
        (-11,  -7),   # back-left
        ( 11,  -7),   # back-right
    ]

    for sx, sy in spike_positions:
        glPushMatrix()
        glTranslatef(sx, sy, 0)

        # Dark red base ring
        glColor3f(0.65, 0.10, 0.10)
        gluDisk(q, 0, 5, 10, 1)

        # Bright red sharp spike pointing straight up
        glColor3f(0.92, 0.15, 0.15)
        gluCylinder(q, 5, 0, 36, 10, 1)

        # Shiny tip highlight — tiny bright cone on top
        glTranslatef(0, 0, 28)
        glColor3f(1.0, 0.55, 0.55)
        gluCylinder(q, 1.5, 0, 10, 6, 1)

        glPopMatrix()

    glPopMatrix()


def draw_rabbit(world_x, world_y, direction, color, hop):
    angle = [0, -90, 180, 90][direction]
    glPushMatrix()
    glTranslatef(world_x, world_y, hop)
    glRotatef(angle, 0, 0, 1)

    # --- BODY — big white box ---
    glColor3f(color[0], color[1], color[2])
    glPushMatrix()
    glTranslatef(0, 0, 18)
    draw_cube_scaled(42, 30, 36)
    draw_box_outline(42, 30, 36)
    glPopMatrix()

    # --- HEAD — white box ---
    glColor3f(color[0], color[1], color[2])
    glPushMatrix()
    glTranslatef(0, 16, 46)
    draw_cube_scaled(36, 30, 30)
    draw_box_outline(36, 30, 30)
    glPopMatrix()

    # --- EARS — tall white ---
    for ex in (-10, 10):
        glColor3f(color[0], color[1], color[2])
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


def make_level(tiles, start, start_facing, carrots_list, portal, trap_list,
               max_cards_level, heights=None, fox=None):
    return {
        "tiles": set(tiles),
        "start": start,
        "start_dir": start_facing,
        "carrots": carrots_list[:],
        "portal": portal,
        "traps": set(trap_list),
        "max_cards": max_cards_level,
        "heights": heights or {},
        "fox": fox
    }



def build_levels():
    global levels
    levels = [

        #l1
        make_level(
            [
                (0,0), (1,0), (2,0),
                (0,1), (2,1),
                (0,2), (1,2), (2,2)
            ],
            (0,0), 1,
            [(1,0), (2,0), (2,1), (2,2)],  #carrots
            (1,2),  #portal
            [],
            10
        ),

        #l2
        make_level(
            [
                (0,0), (1,0), (2,0), (2,1), (2,2), (1,2), (0,2), (1,3), (2,3)
            ],
            (0,0), 1,      
            [(2,0), (2,2), (1,2)],  #carrots
            (2,3),  #portal
            [],
            13
        ),

        #l3
        make_level(
            [
                (0,0), (1,0), (2,0), (3,0),
                (0,1),                 (3,1),
                (0,2), (1,2), (2,2), (3,2),
                (0,3),                 (3,3),
                (0,4), (1,4), (2,4), (3,4)
            ],
            (0,0), 1,
            [(2,0), (3,0), (3,2), (1,4), (3,4)],  #carrots
            (0,4),  #portal
            [],
            16
        ),

        #l4
        make_level(
            [
                (0,0), (1,0), (2,0), (3,0),
                (0,1),        (2,1), (3,1),
                (0,2), (1,2), (2,2),
                (0,3), (1,3), (2,3), (3,3)
            ],
            (0,0), 1,
            [(3,0), (2,1), (1,2)],   #carrots
            (2,3),  #portal
            [(0,2), (3,3)], #traps
            16
        ),
        
        #l5
        make_level(
            [
                (0,0), (1,0), (2,0), (3,0),
                (0,1),        (2,1),
                (0,2), (1,2), (2,2), (3,2),
                              (2,3), (3,3),
                (0,4), (1,4), (2,4), (3,4)
            ],
            (0,0), 1,
            [(3,0), (2,1), (3,2), (1,4), (3,4)],  #carrots
            (0,4),    #portal
            [(1,2), (0,1)],   #traps
            20
        ),

        #l6
        make_level(
            [
                (0,0), (1,0), (2,0), (3,0),
                (0,1),        (3,1),(0,2),
                (3,3), (1,2), (2,2), (3,2),
                (0,4), (1,4), (2,4), (3,4)
            ],
            (0,0), 1,
            [(3,0),(3,2),(3,4)],
            (0,4),
            [(0,1)],
            20,
            fox=(0,2)
        ),

    ]

def recompute_level_center():
    global level_center, camera_radius

    if not walkable_tiles:
        level_center = (0,0)
        return

    min_x = min(t[0] for t in walkable_tiles)
    max_x = max(t[0] for t in walkable_tiles)
    min_y = min(t[1] for t in walkable_tiles)
    max_y = max(t[1] for t in walkable_tiles)

    level_center = (
        (min_x + max_x) * TILE_SIZE / 2,
        (min_y + max_y) * TILE_SIZE / 2
    )

    size = max(max_x - min_x + 1, max_y - min_y + 1)
    camera_radius = 700 + size * 90

def current_level_data():
    return levels[current_level]


def reset_level(level_idx):
    global current_level, walkable_tiles, traps, carrots, portal_tile, start_tile, start_dir, max_cards
    global rabbit_grid_x, rabbit_grid_y, rabbit_dir, visited_tiles, collected, selected_cards
    global executing_cards, current_card_step, current_step_anim, move_start, move_target, current_action
    global hop_height, flash_tile, flash_amount, level_message, state
    global fox_grid_x, fox_grid_y, fox_active, fox_present, fox_dir

    current_level = level_idx
    lvl = levels[level_idx]

    walkable_tiles = set(lvl["tiles"])
    traps = set(lvl["traps"])
    carrots = lvl["carrots"][:]
    portal_tile = lvl["portal"]
    start_tile = lvl["start"]
    start_dir = lvl["start_dir"]
    max_cards = lvl["max_cards"]

    # FOX
    fox_present = lvl["fox"] is not None
    fox_active = False
    if fox_present:
        fox_grid_x, fox_grid_y = lvl["fox"]
        fox_dir = 1

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

def draw_fox(world_x, world_y, direction, hop=0):
    angle = [0, -90, 180, 90][direction]

    glPushMatrix()
    glTranslatef(world_x, world_y, hop)
    glRotatef(angle, 0, 0, 1)

    #tail
    glPushMatrix()
    glTranslatef(-20, -25, 40)
    glRotatef(75, 0, 1, 0)
    glColor3f(0.95, 0.45, 0.08)
    glPushMatrix()
    glScalef(1.4, 0.8, 0.5)
    draw_cube_scaled(44, 30, 44)
    draw_box_outline(44, 30, 44)
    glPopMatrix()
    #white tip
    glColor3f(0.96, 0.94, 0.88)
    glPushMatrix()
    glTranslatef(-20, 0, 0)
    draw_cube_scaled(22, 22, 14)
    glPopMatrix()
    glPopMatrix()

    #body
    glColor3f(0.95, 0.45, 0.08)
    glPushMatrix()
    glTranslatef(0, 0, 28)
    draw_cube_scaled(58, 28, 54)
    draw_box_outline(46, 28, 54)
    glPopMatrix()

    #belly
    glColor3f(0.94, 0.90, 0.80)
    glPushMatrix()
    glTranslatef(0, 16, 28)
    draw_cube_scaled(22, 2, 36) 
    glPopMatrix()

    #neck
    glColor3f(0.95, 0.45, 0.08)
    glPushMatrix()
    glTranslatef(0, 0, 62)
    draw_cube_scaled(24, 20, 16)
    glPopMatrix()

    #head
    glPushMatrix()
    glTranslatef(0, 0, 82)
    glColor3f(0.95, 0.45, 0.08)
    draw_cube_scaled(36, 28, 36)
    draw_box_outline(36, 28, 36)
    glPopMatrix()

    #nose
    glColor3f(0.96, 0.78, 0.58)
    glPushMatrix()
    glTranslatef(0, 14, 82)
    draw_cube_scaled(20, 8, 24)
    draw_box_outline(20, 8, 24)
    glPopMatrix()

    glColor3f(0.08, 0.08, 0.08)
    glPushMatrix()
    glTranslatef(0, 18, 90)
    draw_cube_scaled(8, 4, 8)
    glPopMatrix()

    #ears
    glColor3f(0.95, 0.45, 0.08)
    for ex in (-12, 12):
        glPushMatrix()
        glTranslatef(ex, 0, 108)
        draw_cube_scaled(10, 8, 26)
        draw_box_outline(10, 8, 26)
        glPopMatrix()
        glColor3f(0.95, 0.45, 0.08)

    #legs
    for lx in (-14, 14):
        glColor3f(0.88, 0.38, 0.06)
        glPushMatrix()
        glTranslatef(lx, 0, 14)
        draw_cube_scaled(12, 14, 12)
        glPopMatrix()
        glColor3f(0.12, 0.10, 0.08)
        glPushMatrix()
        glTranslatef(lx, 0, 4)
        draw_cube_scaled(10, 12, 10)
        glPopMatrix()
        
    glPopMatrix()

def fox_can_see_rabbit():
    global fox_grid_x, fox_grid_y, rabbit_grid_x, rabbit_grid_y
    # Facing EAST
    if rabbit_grid_y != fox_grid_y:
        return False
    if rabbit_grid_x <= fox_grid_x:
        return False

    for x in range(fox_grid_x + 1, rabbit_grid_x):
        if (x, fox_grid_y) not in walkable_tiles:
            return False
    return True

def move_fox():
    global fox_grid_x, fox_grid_y, fox_dir, state, level_message

    if not fox_present:
        return

    best = None
    best_dist = 999999

    for i, (dx, dy) in enumerate(DIRS):
        nx = fox_grid_x + dx
        ny = fox_grid_y + dy

        if (nx, ny) not in walkable_tiles:
            continue

        dist = abs(nx - rabbit_grid_x) + abs(ny - rabbit_grid_y)

        if dist < best_dist:
            best_dist = dist
            best = (nx, ny, i)

    if best:
        fox_grid_x, fox_grid_y, fox_dir = best

    if (fox_grid_x, fox_grid_y) == (rabbit_grid_x, rabbit_grid_y):
        state = STATE_GAMEOVER
        level_message = "Fox caught you"

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

    draw_text(450, 720, "Card Hopper",
              GLUT_BITMAP_TIMES_ROMAN_24,
              (0.15, 0.15, 0.15))

    draw_button((620, 470, 840, 540), "P", (0.25, 0.65, 0.35))
    draw_text(705, 440, "Play", color=(1, 1, 1))

    draw_button((620, 350, 840, 420), "C", (0.30, 0.40, 0.85))
    draw_text(655, 320, "Customize Rabbit", color=(1, 1, 1))
    end_2d()


def build_customize_ui():
    begin_2d()
    draw_text(405, 700, "Customize Rabbit", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.92, 0.45))
    draw_text(445, 650, "Pick a color!", color=(1, 1, 1))
    base_x = 240
    for i, col in enumerate(rabbit_colors):
        rect = (base_x + i * 110, 430, base_x + i * 110 + 70, 500)
        draw_rect(rect[0], rect[1], rect[2], rect[3], col, True)
        draw_rect(rect[0] - 3, rect[1] - 3, rect[2] + 3, rect[3] + 3, (1, 1, 0.2) if i == selected_color_index else (1, 1, 1), False)
        register_click("COLOR", rect, i)
    draw_button((290, 200, 460, 260), "BACK", (0.48, 0.24, 0.24))
    draw_button((540, 200, 710, 260), "PLAY", (0.20, 0.65, 0.30))
    end_2d()


def draw_circle_2d(cx, cy, r, color, segments=32):
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        a = deg_to_rad(360.0 / segments * i)
        glVertex2f(cx + cos_approx(a) * r, cy + sin_approx(a) * r)
    glEnd()


def draw_arrow_icon(cx, cy, size=10):
    """Draw a simple right-pointing arrow at (cx,cy)."""
    glColor3f(1, 1, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(cx - size * 0.5, cy - size * 0.7)
    glVertex2f(cx - size * 0.5, cy + size * 0.7)
    glVertex2f(cx + size * 0.8, cy)
    glEnd()


def draw_rotate_icon(cx, cy, clockwise=True):
    """Draw a curved rotate arrow icon."""
    glColor3f(1, 1, 1)
    glLineWidth(3)
    glBegin(GL_LINE_STRIP)
    start = 30 if clockwise else 150
    end   = 300 if clockwise else -120
    steps = 16
    for i in range(steps + 1):
        t = i / steps
        a = deg_to_rad(start + (end - start) * t)
        glVertex2f(cx + cos_approx(a) * 11, cy + sin_approx(a) * 11)
    glEnd()
    glLineWidth(1)
    # arrowhead tip
    tip_a = deg_to_rad(end)
    perp  = deg_to_rad(end + (40 if clockwise else -40))
    tx = cx + cos_approx(tip_a) * 11
    ty = cy + sin_approx(tip_a) * 11
    glBegin(GL_TRIANGLES)
    glVertex2f(tx, ty)
    glVertex2f(tx + cos_approx(perp) * 7, ty + sin_approx(perp) * 7)
    glVertex2f(tx + cos_approx(tip_a + deg_to_rad(180)) * 5,
               ty + sin_approx(tip_a + deg_to_rad(180)) * 5)
    glEnd()


def build_game_ui():
    begin_2d()

    # ── HUD top-left ──────────────────────────────────────────────
    draw_rect(0, WINDOW_H - 115, 370, WINDOW_H, (0.10, 0.12, 0.18), True)
    draw_text(16, WINDOW_H - 28,  "Level %d/6" % (current_level + 1), color=(1, 1, 0.5))
    draw_text(16, WINDOW_H - 52,  "Carrots: %d/%d" % (len(collected), len(carrots)), color=(1, 1, 1))
    draw_text(16, WINDOW_H - 76,  level_message, color=(0.82, 1, 0.82))
    draw_text(16, WINDOW_H - 100, "Cards: %d/%d" % (len(selected_cards), max_cards), color=(1, 1, 1))

    if state == STATE_PAUSED:
        draw_text(430, WINDOW_H - 60, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.7, 0.4))
    elif state == STATE_GAMEOVER:
        draw_text(370, WINDOW_H - 60, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24, (1, 0.35, 0.35))
    elif state == STATE_WIN:
        draw_text(320, WINDOW_H - 60, "YOU FINISHED ALL LEVELS!", GLUT_BITMAP_TIMES_ROMAN_24, (0.65, 1, 0.5))

    # ── CARD STRIP background (green pill) ───────────────────────
    strip_x1 = 30
    strip_x2 = WINDOW_W - 100
    strip_y1 = 14
    strip_y2 = 82
    strip_cx = (strip_x1 + strip_x2) / 2
    strip_cy = (strip_y1 + strip_y2) / 2
    r = (strip_y2 - strip_y1) / 2   # 34

    # pill shape: rect + two semicircles
    glColor3f(0.20, 0.72, 0.25)
    glBegin(GL_QUADS)
    glVertex2f(strip_x1 + r, strip_y1)
    glVertex2f(strip_x2 - r, strip_y1)
    glVertex2f(strip_x2 - r, strip_y2)
    glVertex2f(strip_x1 + r, strip_y2)
    glEnd()
    draw_circle_2d(strip_x1 + r, strip_cy, r, (0.20, 0.72, 0.25))
    draw_circle_2d(strip_x2 - r, strip_cy, r, (0.20, 0.72, 0.25))

    # ── CARD SLOTS inside the strip ───────────────────────────────
    slot_colors = {
        CARD_FORWARD: (0.10, 0.55, 0.20),
        CARD_LEFT:    (0.10, 0.55, 0.20),
        CARD_RIGHT:   (0.10, 0.55, 0.20),
        CARD_WAIT:    (0.10, 0.55, 0.20),
    }
    slot_w = 52
    slot_gap = 14      # gap between slots (for the separator arrows)
    slot_start = strip_x1 + r + 8
    num_visible = min(MAX_VISIBLE_CARDS, max_cards)

    for i in range(num_visible):
        actual_index = i + card_view_offset

        sx = slot_start + i * (slot_w + slot_gap)
        sy1, sy2 = strip_y1 + 6, strip_y2 - 6
        scx = sx + slot_w / 2
        scy = (sy1 + sy2) / 2

        if actual_index < len(selected_cards):
            card = selected_cards[actual_index]

            col = (0.12, 0.48, 0.18)
            draw_rect(sx, sy1, sx + slot_w, sy2, col, True)

            # draw icon
            if card == CARD_FORWARD:
                draw_arrow_icon(scx, scy, 10)
            elif card == CARD_LEFT:
                draw_rotate_icon(scx, scy, clockwise=False)
            elif card == CARD_RIGHT:
                draw_rotate_icon(scx, scy, clockwise=True)
            else:
                draw_text(sx + 8, scy - 6, "W", color=(1, 1, 1))

            # highlight executing card
            if executing_cards and actual_index == current_card_step:
                draw_rect(sx - 2, sy1 - 2, sx + slot_w + 2, sy2 + 2, (1, 1, 0.2), False)

            register_click(card, (sx, sy1, sx + slot_w, sy2), actual_index)
        else:
            draw_rect(sx, sy1, sx + slot_w, sy2, (0.12, 0.52, 0.18), True)
            draw_rect(sx, sy1, sx + slot_w, sy2, (0.08, 0.38, 0.12), False)
        # separator arrow between slots
        if i < num_visible - 1:
            ax = sx + slot_w + slot_gap / 2
            draw_arrow_icon(ax, scy, 6)

    # ── ORANGE PLAY BUTTON (big circle, right of strip) ──────────
    play_cx = WINDOW_W - 52
    play_cy = strip_cy
    play_r  = 34

    # shadow/dark ring
    draw_circle_2d(play_cx, play_cy, play_r + 3, (0.55, 0.28, 0.00))
    # main orange circle
    draw_circle_2d(play_cx, play_cy, play_r, (0.95, 0.52, 0.05))
    # play triangle inside
    glColor3f(1, 1, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(play_cx - 10, play_cy - 16)
    glVertex2f(play_cx - 10, play_cy + 16)
    glVertex2f(play_cx + 16, play_cy)
    glEnd()
    register_click(CARD_PLAY, (play_cx - play_r, play_cy - play_r,
                               play_cx + play_r, play_cy + play_r))

    # ── TOOL CARDS (bottom-left, below strip) ────────────────────
    tool_colors = {
        CARD_FORWARD: (0.20, 0.72, 0.25),
        CARD_LEFT:    (0.20, 0.72, 0.25),
        CARD_RIGHT:   (0.20, 0.72, 0.25),
        CARD_WAIT:    (0.55, 0.30, 0.80),
    }
    # Only show FWD and LEFT/RIGHT as two tool buttons (like doodle)
    TOOL_DISPLAY = [
        (CARD_FORWARD, "FWD"),
        (CARD_LEFT,    "LFT"),
        (CARD_RIGHT,   "RGT"),
        (CARD_WAIT,    "STP"),
    ]
    tool_btn_w  = 64
    tool_btn_h  = 52
    tool_gap    = 12
    tool_total  = len(TOOL_DISPLAY) * tool_btn_w + (len(TOOL_DISPLAY) - 1) * tool_gap
    tool_start_x = (WINDOW_W - tool_total) // 2   # centered horizontally
    tool_y1 = strip_y2 + 10
    tool_y2 = tool_y1 + tool_btn_h

    btn_colors = {
        CARD_FORWARD: (0.20, 0.72, 0.25),
        CARD_LEFT:    (0.20, 0.72, 0.25),
        CARD_RIGHT:   (0.20, 0.72, 0.25),
        CARD_WAIT:    (0.55, 0.30, 0.80),
    }
    border_colors = {
        CARD_FORWARD: (0.10, 0.45, 0.12),
        CARD_LEFT:    (0.10, 0.45, 0.12),
        CARD_RIGHT:   (0.10, 0.45, 0.12),
        CARD_WAIT:    (0.35, 0.15, 0.55),
    }
    labels = {
        CARD_FORWARD: "Forward",
        CARD_LEFT:    "Left",
        CARD_RIGHT:   "Right",
        CARD_WAIT:    "Wait",
    }

    for i, (card, _) in enumerate(TOOL_DISPLAY):
        bx = tool_start_x + i * (tool_btn_w + tool_gap)
        bcx = bx + tool_btn_w / 2
        bcy = (tool_y1 + tool_y2) / 2

        # button background
        draw_rect(bx, tool_y1, bx + tool_btn_w, tool_y2, btn_colors[card], True)
        draw_rect(bx, tool_y1, bx + tool_btn_w, tool_y2, border_colors[card], False)

        # icon inside button
        if card == CARD_FORWARD:
            draw_arrow_icon(bcx, bcy + 4, 11)
        elif card == CARD_LEFT:
            draw_rotate_icon(bcx, bcy + 4, clockwise=False)
        elif card == CARD_RIGHT:
            draw_rotate_icon(bcx, bcy + 4, clockwise=True)
        elif card == CARD_WAIT:
            # two vertical bars = pause/wait icon
            glColor3f(1, 1, 1)
            draw_rect(bcx - 8, bcy - 6, bcx - 2, bcy + 10, (1, 1, 1), True)
            draw_rect(bcx + 2, bcy - 6, bcx + 8, bcy + 10, (1, 1, 1), True)

        # label below icon
        draw_text(bx + tool_btn_w // 2 - len(labels[card]) * 3,
                  tool_y1 + 6, labels[card],
                  font=GLUT_BITMAP_HELVETICA_12,
                  color=(1, 1, 1))

        register_click(card, (bx, tool_y1, bx + tool_btn_w, tool_y2), card)


    # also register hidden clicks for RIGHT and WAIT (keyboard/cheat use)
    for c in [CARD_RIGHT, CARD_WAIT]:
        register_click(c, (0, 0, 0, 0), c)

    # ── CLEAR button ─────────────────────────────────────────────
    draw_button((WINDOW_W - 190, strip_y2 + 12, WINDOW_W - 100, strip_y2 + 52),
                CARD_CLEAR, (0.70, 0.20, 0.20))

    end_2d()


def handle_ui_click(mx, my):
    global state, selected_color_index, saved_color_index, selected_cards, level_message, card_view_offset
    for name, rect, extra in click_regions:
        if not inside_rect(mx, my, rect):
            continue
        if name == "MENU":
            state = STATE_MENU
            return
        if name == "RESTART" and state in (STATE_FAILED, STATE_GAMEOVER, STATE_WIN):
            restart_current_level()
            return
        if name == "RETRY" and state == STATE_FAILED:
            saved = selected_cards[:]
            restart_current_level()
            selected_cards = saved
            start_card_execution()
            return

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
            if name == "PLAY":
                saved_color_index = selected_color_index
                reset_level(0)
                return

        elif state == STATE_PLAYING:
            if name in TOOL_CARDS and not executing_cards:
                if extra is not None and isinstance(extra, int):
                    if 0 <= extra < len(selected_cards):
                        selected_cards.pop(extra)
                        if card_view_offset > 0:
                            card_view_offset -= 1
                        level_message = "Card removed"
                elif len(selected_cards) < max_cards:
                    selected_cards.append(name)
                    if len(selected_cards) > MAX_VISIBLE_CARDS:
                        card_view_offset += 1
                    level_message = "Card added"
                return
            if name == CARD_PLAY and not executing_cards and selected_cards:
                start_card_execution()
                return
            if name == CARD_CLEAR and not executing_cards:
                selected_cards = []
                card_view_offset = 0
                level_message = "Sequence cleared"
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


def update_execution(dt=16):
    global executing_cards, current_card_step, current_step_anim, current_action, hop_height, state, level_message

    if not executing_cards or state != STATE_PLAYING:
        return
    if current_card_step >= len(selected_cards):
        executing_cards = False
        current_action = ""
        hop_height = 0.0
        if state == STATE_PLAYING:
            if not (all_carrots_collected() and (rabbit_grid_x, rabbit_grid_y) == portal_tile):
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

        # FOX ACTIVATION
        global fox_active
        if fox_present and not fox_active:
            if fox_can_see_rabbit():
                fox_active = True

        # FOX MOVES ONLY WHEN RABBIT HOPS
        if fox_present and fox_active:
            move_fox()

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
    global cheat_message_timer, carrot_bob_time,portal_angle
    update_execution()
    update_flash()
    update_clouds()
    carrot_bob_time += 0.04   # add this line
    portal_angle += 1.2  
    glutPostRedisplay()

def draw_tree(wx, wy, base_z):
    glPushMatrix()
    glTranslatef(wx, wy, base_z)

    # Bottom base block (yellow-green, large)
    glColor3f(0.55, 0.78, 0.22)
    glPushMatrix()
    glTranslatef(0, 0, 8)
    draw_cube_scaled(44, 44, 16)
    draw_box_outline(44, 44, 16)
    glPopMatrix()

    # Middle block (teal/blue, slightly smaller)
    glColor3f(0.20, 0.62, 0.72)
    glPushMatrix()
    glTranslatef(0, 0, 24)
    draw_cube_scaled(36, 36, 16)
    draw_box_outline(36, 36, 16)
    glPopMatrix()

    # Trunk (thin, dark)
    glColor3f(0.30, 0.18, 0.08)
    glPushMatrix()
    glTranslatef(0, 0, 44)
    draw_cube_scaled(10, 10, 55)
    draw_box_outline(10, 10, 55)
    glPopMatrix()

    # Top foliage block (big bright green square)
    glColor3f(0.22, 0.75, 0.30)
    glPushMatrix()
    glTranslatef(0, 0, 105)
    draw_cube_scaled(46, 46, 36)
    draw_box_outline(46, 46, 36)
    glPopMatrix()

    # Smaller top cap (darker green)
    glColor3f(0.15, 0.58, 0.22)
    glPushMatrix()
    glTranslatef(0, 0, 130)
    draw_cube_scaled(30, 30, 22)
    draw_box_outline(30, 30, 22)
    glPopMatrix()

    glPopMatrix()

def draw_level_scene():
    for gx, gy in walkable_tiles:
        base = (0.29, 0.78, 0.65) if (gx + gy) % 2 == 0 else (0.22, 0.68, 0.58)
        if (gx, gy) in visited_tiles:
            base = (0.75, 0.65, 0.85) 
        if flash_tile == (gx, gy) and flash_amount > 0:
            boost = flash_amount * 0.3
            base = (min(base[0] + boost, 1), min(base[1] + boost, 1), min(base[2] + boost, 1))
        tile_height = current_level_data().get("heights", {}).get((gx, gy), 1)
        draw_tile(gx, gy, base, height=tile_height)

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
        h_start = current_level_data().get("heights", {}).get(
            (int(round(move_start[0])), int(round(move_start[1]))), 1)
        h_end   = current_level_data().get("heights", {}).get(
            (int(round(move_target[0])), int(round(move_target[1]))), 1)
        tile_z  = (h_start + (h_end - h_start) * t) * 16
    else:
        draw_x = float(rabbit_grid_x)
        draw_y = float(rabbit_grid_y)
        tile_z = current_level_data().get("heights", {}).get(
            (rabbit_grid_x, rabbit_grid_y), 1) * 16

    wx, wy = grid_to_world(draw_x, draw_y)
    if fox_present:
        fz = current_level_data().get("heights", {}).get((fox_grid_x, fox_grid_y), 1) * 16
        fwx, fwy = grid_to_world(fox_grid_x, fox_grid_y)
        draw_fox(fwx, fwy, fox_dir, fz)
    tree_positions = [(-3, -1),(-3,  2),( 5, -1),( 5,  2),]
    for tx, ty in tree_positions:
        twx, twy = grid_to_world(tx, ty)
        draw_tree(twx, twy, 0)

    draw_rabbit(wx, wy, rabbit_dir, rabbit_colors[saved_color_index], hop_height + tile_z)
                
def draw_customize_preview():
    set_static_menu_camera()

    glPushMatrix()
    glScalef(1.6, 1.6, 1.6)
    draw_rabbit(50, -80, 1, rabbit_colors[selected_color_index], 0)
    glPopMatrix()

def show_failed_overlay():
    begin_2d()

    glColor4f(0.0, 0.0, 0.0, 0.45)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(WINDOW_W, 0)
    glVertex2f(WINDOW_W, WINDOW_H); glVertex2f(0, WINDOW_H)
    glEnd()
    glDisable(GL_BLEND)

    draw_rect(306, 244, 706, 524, (0.04, 0.04, 0.08), True)
    draw_rect(300, 250, 700, 520, (0.12, 0.14, 0.22), True)
    draw_rect(300, 514, 700, 520, (0.85, 0.20, 0.20), True)
    draw_rect(300, 250, 700, 520, (0.75, 0.22, 0.22), False)

    draw_text(388, 480, "FAILED!", GLUT_BITMAP_TIMES_ROMAN_24, (1.0, 0.28, 0.28))
    draw_text(308, 440, "Sequence did not finish the level", color=(0.88, 0.88, 0.95))

    glColor3f(0.28, 0.30, 0.42)
    glBegin(GL_LINES)
    glVertex2f(320, 425); glVertex2f(680, 425)
    glEnd()

    draw_rect(320, 375, 680, 415, (0.72, 0.16, 0.16), True)
    draw_rect(320, 375, 680, 415, (1.0, 0.48, 0.48), False)
    draw_text(380, 388, "R  —  Restart Level", color=(1, 1, 1))
    register_click("RESTART", (320, 375, 680, 415))

    draw_rect(320, 325, 680, 365, (0.16, 0.46, 0.80), True)
    draw_rect(320, 325, 680, 365, (0.48, 0.78, 1.00), False)
    draw_text(342, 338, "P  —  Try Same Sequence Again", color=(1, 1, 1))
    register_click("RETRY", (320, 325, 680, 365))

    draw_rect(320, 272, 680, 312, (0.25, 0.25, 0.35), True)
    draw_rect(320, 272, 680, 312, (0.60, 0.60, 0.80), False)
    draw_text(375, 285, "M  —  Back to Menu", color=(0.85, 0.85, 1.0))
    register_click("MENU", (320, 272, 680, 312))

    end_2d()

def show_gameover_overlay():
    begin_2d()
    glColor4f(0.0, 0.0, 0.0, 0.50)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(WINDOW_W, 0)
    glVertex2f(WINDOW_W, WINDOW_H); glVertex2f(0, WINDOW_H)
    glEnd()
    glDisable(GL_BLEND)
    draw_rect(306, 264, 706, 514, (0.05, 0.03, 0.03), True)
    draw_rect(300, 270, 700, 510, (0.16, 0.10, 0.10), True)
    draw_rect(300, 504, 700, 510, (0.95, 0.18, 0.10), True)
    draw_rect(300, 270, 700, 510, (0.95, 0.22, 0.12), False)
    draw_text(355, 470, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24, (1.0, 0.22, 0.12))
    draw_text(340, 430, level_message, color=(0.95, 0.72, 0.72)) 
    draw_rect(320, 365, 680, 405, (0.72, 0.16, 0.16), True)
    draw_rect(320, 365, 680, 405, (1.0, 0.48, 0.48), False)
    draw_text(380, 378, "R  —  Restart Level", color=(1, 1, 1))
    register_click("RESTART", (320, 365, 680, 405))
    draw_rect(320, 312, 680, 352, (0.25, 0.25, 0.35), True)
    draw_rect(320, 312, 680, 352, (0.60, 0.60, 0.80), False)
    draw_text(375, 325, "M  —  Back to Menu", color=(0.85, 0.85, 1.0))
    register_click("MENU", (320, 312, 680, 352))
    end_2d()

def show_win_overlay():
    begin_2d()
    glColor4f(0.0, 0.0, 0.0, 0.40)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    glVertex2f(0, 0); glVertex2f(WINDOW_W, 0)
    glVertex2f(WINDOW_W, WINDOW_H); glVertex2f(0, WINDOW_H)
    glEnd()
    glDisable(GL_BLEND)
    draw_rect(256, 244, 756, 524, (0.04, 0.08, 0.05), True)
    draw_rect(250, 250, 750, 520, (0.10, 0.16, 0.12), True)
    draw_rect(250, 514, 750, 520, (0.22, 0.88, 0.38), True)
    draw_rect(250, 250, 750, 520, (0.22, 0.88, 0.40), False)
    draw_text(330, 480, "YOU WIN!", GLUT_BITMAP_TIMES_ROMAN_24, (0.35, 1.0, 0.52))
    draw_text(280, 440, "All levels complete! Great job!", color=(0.78, 1.0, 0.84))
    draw_rect(270, 375, 730, 415, (0.18, 0.62, 0.32), True)
    draw_rect(270, 375, 730, 415, (0.35, 1.00, 0.52), False)
    draw_text(375, 388, "P  —  Back to Menu", color=(1, 1, 1))
    register_click("MENU", (270, 375, 730, 415))
    draw_rect(270, 320, 730, 360, (0.18, 0.42, 0.72), True)
    draw_rect(270, 320, 730, 360, (0.48, 0.78, 1.00), False)
    draw_text(375, 333, "R  —  Play Again", color=(1, 1, 1))
    register_click("RESTART", (270, 320, 730, 360))
    end_2d()

def set_static_menu_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_W / float(WINDOW_H), 1.0, 5000.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    gluLookAt(
        520, -760, 520,   # eye
        0, 0, 80,         # target
        0, 0, 1
    )
def draw_menu_island():

    # Dirt blocks
    for x in range(-2, 3):
        for y in range(-2, 3):
            draw_tile(x, y, (0.52, 0.38, 0.22), 2)

    # Grass top
    for x in range(-2, 3):
        for y in range(-2, 3):
            wx, wy = grid_to_world(x, y)

            glColor3f(0.25, 0.78, 0.30)
            glBegin(GL_QUADS)
            glVertex3f(wx-44, wy-44, 33)
            glVertex3f(wx+44, wy-44, 33)
            glVertex3f(wx+44, wy+44, 33)
            glVertex3f(wx-44, wy+44, 33)
            glEnd()
    for cloud in clouds:
        cx, cy, cz = cloud["x"], cloud["y"], cloud["z"]

        glPushMatrix()
        glTranslatef(cx, cy, cz)

        glColor3f(0.95, 0.95, 0.95)

        # center
        draw_cube_scaled(70, 45, 35)

        # surrounding puffs
        offsets = [
            (40, 0, 10),
            (-40, 0, 5),
            (0, 30, 15),
            (0, -30, 8),
            (25, 20, 12),
            (-25, -20, 10),
        ]

        for ox, oy, oz in offsets:
            glPushMatrix()
            glTranslatef(ox, oy, oz)
            draw_cube_scaled(45, 30, 25)
            glPopMatrix()

        glPopMatrix()

def update_clouds():
    global cloud_time
    cloud_time += 0.002  # speed of animation

    amplitude = 20      # how high they move

    for cloud in clouds:
        t = cloud_time + cloud["phase"]
        cloud["z"] = cloud["base_z"] + sin_approx(t) * amplitude

def showScreen():
    global click_regions
    click_regions = []
    glClearColor(0.38, 0.88, 0.84, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_W, WINDOW_H)

    if state == STATE_MENU:
        set_static_menu_camera()

        draw_menu_island()

        glPushMatrix()
        glTranslatef(40, -20, 34)
        glScalef(1.75, 1.75, 1.75)
        draw_rabbit(0, 0, 1, rabbit_colors[saved_color_index], 0)
        glPopMatrix()

        build_menu_ui()
    elif state == STATE_CUSTOMIZE:
        draw_customize_preview()
        build_customize_ui()
    else:
        set_perspective_camera()
        draw_level_scene()
        build_game_ui()
        if state == STATE_FAILED:
            show_failed_overlay()
        elif state == STATE_GAMEOVER:
            show_gameover_overlay()
        elif state == STATE_WIN:
            show_win_overlay()

    glutSwapBuffers()


def main():
    build_levels()
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_W, WINDOW_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Project Group_2")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()


if __name__ == "__main__":
    main()
