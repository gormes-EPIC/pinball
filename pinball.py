import pygame
import sys
import math
import random

WIDTH, HEIGHT = 1024, 600
FPS = 60
GRAVITY = 0.28
BALL_RADIUS = 10
FLIPPER_LENGTH = 88
FLIPPER_THICKNESS = 7

# Field boundaries
WALL_LEFT = 52
WALL_RIGHT = WIDTH - 52
WALL_TOP = 38

# Flipper positions
FLIPPER_Y = HEIGHT - 85
LEFT_PIVOT = (WIDTH // 2 - 98, FLIPPER_Y)
RIGHT_PIVOT = (WIDTH // 2 + 98, FLIPPER_Y)
GUIDE_START_Y = 375   # height on the side walls where the angled sections begin
LEFT_FLIP_REST = 35
LEFT_FLIP_ACTIVE = -35
RIGHT_FLIP_REST = 145
RIGHT_FLIP_ACTIVE = 215

# Colors
WHITE = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (60, 220, 60)
BLUE = (50, 110, 220)
YELLOW = (255, 220, 0)
ORANGE = (255, 150, 0)
PURPLE = (180, 50, 220)
CYAN = (0, 210, 230)
GRAY = (120, 120, 130)
DARK = (20, 20, 40)
NAVY = (15, 15, 50)
LIGHT_GRAY = (190, 190, 200)
WALL_COLOR = (70, 70, 90)


def line_ball_collide(ball, x1, y1, x2, y2, restitution=0.65):
    dx, dy = x2 - x1, y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq < 1:
        return False
    t = max(0.0, min(1.0, ((ball.x - x1) * dx + (ball.y - y1) * dy) / len_sq))
    cx, cy = x1 + t * dx, y1 + t * dy
    dist_x, dist_y = ball.x - cx, ball.y - cy
    dist = math.sqrt(dist_x * dist_x + dist_y * dist_y)
    if 0.001 < dist < BALL_RADIUS:
        nx, ny = dist_x / dist, dist_y / dist
        ball.x += nx * (BALL_RADIUS - dist)
        ball.y += ny * (BALL_RADIUS - dist)
        dot = ball.vx * nx + ball.vy * ny
        if dot < 0:
            ball.vx -= (1 + restitution) * dot * nx
            ball.vy -= (1 + restitution) * dot * ny
        return True
    return False


class Ball:
    def __init__(self):
        self.x = float(WIDTH // 2 + random.randint(-20, 20))
        self.y = float(FLIPPER_Y - 120)
        angle = random.uniform(-100, -80)
        speed = random.uniform(8, 10)
        self.vx = speed * math.cos(math.radians(angle))
        self.vy = speed * math.sin(math.radians(angle))

    def sub_step(self, dt):
        self.vy += GRAVITY * dt
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > 16:
            self.vx = self.vx / speed * 16
            self.vy = self.vy / speed * 16
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x - BALL_RADIUS < WALL_LEFT:
            self.x = WALL_LEFT + BALL_RADIUS
            self.vx = abs(self.vx) * 0.82
        elif self.x + BALL_RADIUS > WALL_RIGHT:
            self.x = WALL_RIGHT - BALL_RADIUS
            self.vx = -abs(self.vx) * 0.82
        if self.y - BALL_RADIUS < WALL_TOP:
            self.y = WALL_TOP + BALL_RADIUS
            self.vy = abs(self.vy) * 0.82

    def is_lost(self):
        return self.y > HEIGHT + BALL_RADIUS * 2

    def draw(self, surface):
        px, py = int(self.x), int(self.y)
        pygame.draw.circle(surface, LIGHT_GRAY, (px, py), BALL_RADIUS)
        pygame.draw.circle(surface, WHITE, (px - 3, py - 3), BALL_RADIUS // 3)


class Flipper:
    def __init__(self, pivot, rest_angle, active_angle):
        self.px, self.py = float(pivot[0]), float(pivot[1])
        self.rest_angle = rest_angle
        self.active_angle = active_angle
        self.angle = float(rest_angle)
        self.prev_angle = float(rest_angle)
        self.pressed = False

    def update(self):
        self.prev_angle = self.angle
        target = self.active_angle if self.pressed else self.rest_angle
        self.angle += (target - self.angle) * (0.38 if self.pressed else 0.28)

    @property
    def angular_velocity(self):
        return self.angle - self.prev_angle

    def get_tip(self):
        rad = math.radians(self.angle)
        return self.px + math.cos(rad) * FLIPPER_LENGTH, self.py + math.sin(rad) * FLIPPER_LENGTH

    def collide(self, ball):
        tx, ty = self.get_tip()
        dx, dy = tx - self.px, ty - self.py
        len_sq = dx * dx + dy * dy
        if len_sq < 1:
            return False

        t = max(0.0, min(1.0, ((ball.x - self.px) * dx + (ball.y - self.py) * dy) / len_sq))
        cx = self.px + t * dx
        cy = self.py + t * dy
        dist_x, dist_y = ball.x - cx, ball.y - cy
        dist = math.sqrt(dist_x * dist_x + dist_y * dist_y)
        hit_dist = BALL_RADIUS + FLIPPER_THICKNESS

        if dist >= hit_dist or dist < 0.001:
            return False

        nx, ny = dist_x / dist, dist_y / dist
        ball.x += nx * (hit_dist - dist)
        ball.y += ny * (hit_dist - dist)

        r_dist = t * FLIPPER_LENGTH
        av_rad = math.radians(self.angular_velocity)
        angle_rad = math.radians(self.angle)
        wall_vx = -r_dist * math.sin(angle_rad) * av_rad
        wall_vy = r_dist * math.cos(angle_rad) * av_rad

        rel_vx = ball.vx - wall_vx
        rel_vy = ball.vy - wall_vy
        dot = rel_vx * nx + rel_vy * ny

        if dot < 0:
            restitution = 0.72
            ball.vx -= (1 + restitution) * dot * nx
            ball.vy -= (1 + restitution) * dot * ny
            speed = math.sqrt(ball.vx ** 2 + ball.vy ** 2)
            if speed > 16:
                ball.vx = ball.vx / speed * 16
                ball.vy = ball.vy / speed * 16
        return True

    def draw(self, surface):
        tx, ty = self.get_tip()
        rad = math.radians(self.angle)
        dx, dy = math.cos(rad), math.sin(rad)
        nx, ny = -dy * FLIPPER_THICKNESS, dx * FLIPPER_THICKNESS
        pts = [
            (self.px + nx, self.py + ny),
            (tx + nx * 0.55, ty + ny * 0.55),
            (tx - nx * 0.55, ty - ny * 0.55),
            (self.px - nx, self.py - ny),
        ]
        color = (100, 255, 100) if self.pressed else GREEN
        pygame.draw.polygon(surface, color, [(int(p[0]), int(p[1])) for p in pts])
        pygame.draw.circle(surface, color, (int(self.px), int(self.py)), FLIPPER_THICKNESS + 2)
        pygame.draw.circle(surface, color, (int(tx), int(ty)), FLIPPER_THICKNESS - 1)


class Bumper:
    def __init__(self, x, y, radius, color, points):
        self.x, self.y = x, y
        self.radius = radius
        self.color = color
        self.points = points
        self.hit_timer = 0
        self.pulse = random.uniform(0, math.pi * 2)

    def update(self):
        if self.hit_timer > 0:
            self.hit_timer -= 1
        self.pulse = (self.pulse + 0.04) % (math.pi * 2)

    def collide(self, ball):
        dx, dy = ball.x - self.x, ball.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        min_d = BALL_RADIUS + self.radius
        if dist < min_d and dist > 0.001:
            nx, ny = dx / dist, dy / dist
            ball.x = self.x + nx * min_d
            ball.y = self.y + ny * min_d
            speed = math.sqrt(ball.vx ** 2 + ball.vy ** 2)
            kick = max(speed * 1.08, 7.5)
            ball.vx = nx * kick
            ball.vy = ny * kick
            self.hit_timer = 14
            return True
        return False

    def draw(self, surface):
        lit = self.hit_timer > 0
        pulse_r = int(self.radius + 3 * math.sin(self.pulse))
        body = WHITE if lit else self.color
        glow = tuple(min(255, c + 50) for c in self.color)
        pygame.draw.circle(surface, glow, (int(self.x), int(self.y)), pulse_r + 5)
        pygame.draw.circle(surface, body, (int(self.x), int(self.y)), pulse_r)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), pulse_r, 2)
        inner = pulse_r // 2
        pygame.draw.circle(surface, self.color if lit else (5, 5, 20), (int(self.x), int(self.y)), inner)


class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 5)
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = random.randint(18, 38)
        self.max_life = self.life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12
        self.vx *= 0.97
        self.life -= 1

    def draw(self, surface):
        a = self.life / self.max_life
        r = max(1, int(3 * a))
        c = tuple(int(ch * a) for ch in self.color)
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), r)


class Popup:
    def __init__(self, x, y, value, font):
        self.x, self.y = float(x), float(y)
        self.value = value
        self.life = 48
        self.font = font

    def update(self):
        self.y -= 0.9
        self.life -= 1

    def draw(self, surface):
        a = min(1.0, self.life / 48)
        color = (255, int(220 * a), 0)
        text = self.font.render(f"+{self.value}", True, color)
        surface.blit(text, (int(self.x) - text.get_width() // 2, int(self.y)))


class Game:
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pinball")
        self.clock = pygame.time.Clock()

        self.font_xl = pygame.font.Font(None, 82)
        self.font_lg = pygame.font.Font(None, 54)
        self.font_md = pygame.font.Font(None, 38)
        self.font_sm = pygame.font.Font(None, 24)

        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Controller: {self.joystick.get_name()}")
            print(f"  Axes: {self.joystick.get_numaxes()}, Buttons: {self.joystick.get_numbuttons()}")

        self.high_score = 0
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.particles = []
        self.popups = []
        self.game_over = False
        self._setup_field()
        self.ball = Ball()

    def _setup_field(self):
        self.left_flipper = Flipper(LEFT_PIVOT, LEFT_FLIP_REST, LEFT_FLIP_ACTIVE)
        self.right_flipper = Flipper(RIGHT_PIVOT, RIGHT_FLIP_REST, RIGHT_FLIP_ACTIVE)

        cx = WIDTH // 2
        self.bumpers = [
            Bumper(cx,       125, 24, YELLOW,  200),
            Bumper(cx - 115, 185, 22, RED,     100),
            Bumper(cx + 115, 185, 22, BLUE,    100),
            Bumper(cx - 58,  268, 20, ORANGE,  150),
            Bumper(cx + 58,  268, 20, PURPLE,  150),
            Bumper(cx - 195, 148, 18, CYAN,    120),
            Bumper(cx + 195, 148, 18, GREEN,   120),
        ]

        lx, ly = LEFT_PIVOT
        rx, ry = RIGHT_PIVOT
        self.guide_rails = [
            (WALL_LEFT, GUIDE_START_Y, lx, ly),
            (WALL_RIGHT, GUIDE_START_Y, rx, ry),
        ]

    def spawn_particles(self, x, y, color, n=10):
        for _ in range(n):
            self.particles.append(Particle(x, y, color))

    def handle_input(self):
        left = False
        right = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_z] or keys[pygame.K_LSHIFT]:
            left = True
        if keys[pygame.K_x] or keys[pygame.K_RSHIFT]:
            right = True

        if self.joystick:
            num_buttons = self.joystick.get_numbuttons()
            num_axes = self.joystick.get_numaxes()

            if num_buttons > 6 and self.joystick.get_button(6):
                left = True
            if num_buttons > 7 and self.joystick.get_button(7):
                right = True

            # Left trigger (axis 2 on most gamepads)
            if num_axes > 2 and self.joystick.get_axis(2) > 0.15:
                left = True
            # Right trigger (axis 5 on most gamepads)
            if num_axes > 5 and self.joystick.get_axis(5) > 0.15:
                right = True

        self.left_flipper.pressed = left
        self.right_flipper.pressed = right

    def update(self):
        self.handle_input()
        self.left_flipper.update()
        self.right_flipper.update()

        # Sub-step physics so the ball can't tunnel through thin surfaces at high speed.
        # Max ball speed is 16 px/frame; 4 steps → ≤4 px/step, well under the 17 px collision zone.
        SUB_STEPS = 4
        dt = 1.0 / SUB_STEPS
        for _ in range(SUB_STEPS):
            self.ball.sub_step(dt)
            self.left_flipper.collide(self.ball)
            self.right_flipper.collide(self.ball)
            for rail in self.guide_rails:
                line_ball_collide(self.ball, *rail)

        for b in self.bumpers:
            b.update()
            if b.collide(self.ball):
                self.score += b.points
                if self.score > self.high_score:
                    self.high_score = self.score
                self.spawn_particles(self.ball.x, self.ball.y, b.color)
                self.popups.append(Popup(b.x, b.y - b.radius - 5, b.points, self.font_sm))

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

        for popup in self.popups[:]:
            popup.update()
            if popup.life <= 0:
                self.popups.remove(popup)

        if self.ball.is_lost():
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.ball = Ball()

    def draw_field(self):
        self.screen.fill(DARK)
        pygame.draw.rect(self.screen, NAVY,
                         (WALL_LEFT, WALL_TOP, WALL_RIGHT - WALL_LEFT, HEIGHT - WALL_TOP))

        # Subtle grid
        for y in range(WALL_TOP, HEIGHT, 44):
            pygame.draw.line(self.screen, (22, 22, 48), (WALL_LEFT, y), (WALL_RIGHT, y))
        for x in range(WALL_LEFT, WALL_RIGHT, 44):
            pygame.draw.line(self.screen, (22, 22, 48), (x, WALL_TOP), (x, HEIGHT))

        # Walls (side panels)
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, WALL_LEFT, HEIGHT))
        pygame.draw.rect(self.screen, WALL_COLOR, (WALL_RIGHT, 0, WIDTH - WALL_RIGHT, HEIGHT))
        pygame.draw.rect(self.screen, WALL_COLOR, (0, 0, WIDTH, WALL_TOP))

        # Solid angled wall sections in the lower corners — triangles pointing inward toward flippers
        lx, ly = LEFT_PIVOT
        rx, ry = RIGHT_PIVOT
        pygame.draw.polygon(self.screen, WALL_COLOR, [
            (WALL_LEFT, GUIDE_START_Y),
            (WALL_LEFT, HEIGHT),
            (lx, ly),
        ])
        pygame.draw.polygon(self.screen, WALL_COLOR, [
            (WALL_RIGHT, GUIDE_START_Y),
            (WALL_RIGHT, HEIGHT),
            (rx, ry),
        ])

        # Main wall edge highlights
        pygame.draw.line(self.screen, LIGHT_GRAY, (WALL_LEFT, WALL_TOP), (WALL_LEFT, GUIDE_START_Y), 2)
        pygame.draw.line(self.screen, LIGHT_GRAY, (WALL_RIGHT, WALL_TOP), (WALL_RIGHT, GUIDE_START_Y), 2)
        pygame.draw.line(self.screen, LIGHT_GRAY, (WALL_LEFT, WALL_TOP), (WALL_RIGHT, WALL_TOP), 2)

        # Angled guide edge highlights (inner face of each lower wall)
        pygame.draw.line(self.screen, LIGHT_GRAY, (WALL_LEFT, GUIDE_START_Y), (lx, ly), 3)
        pygame.draw.line(self.screen, LIGHT_GRAY, (WALL_RIGHT, GUIDE_START_Y), (rx, ry), 3)

        # Drain zone between flipper pivots
        pygame.draw.rect(self.screen, (8, 4, 18),
                         (lx, ly + FLIPPER_THICKNESS + 4, rx - lx, HEIGHT - ly))

    def draw_hud(self):
        score_surf = self.font_xl.render(f"{self.score:,}", True, WHITE)
        self.screen.blit(score_surf, (WIDTH // 2 - score_surf.get_width() // 2, 2))

        if self.high_score > 0 and not self.game_over:
            hs = self.font_sm.render(f"BEST {self.high_score:,}", True, YELLOW)
            self.screen.blit(hs, (8, 6))

        for i in range(self.lives):
            bx = WIDTH - 20 - i * 22
            pygame.draw.circle(self.screen, WHITE, (bx, 16), 8)

        if not self.joystick:
            hint = self.font_sm.render("No controller detected  |  Z / LShift = left    X / RShift = right", True, GRAY)
        else:
            name = self.joystick.get_name()[:28]
            hint = self.font_sm.render(f"{name}  |  Btn6/L-Trigger = left    Btn7/R-Trigger = right", True, GRAY)
        self.screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 17))

    def draw_game_over(self):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(175)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        go = self.font_xl.render("GAME OVER", True, RED)
        self.screen.blit(go, (WIDTH // 2 - go.get_width() // 2, HEIGHT // 2 - 90))

        sc = self.font_lg.render(f"Score: {self.score:,}", True, WHITE)
        self.screen.blit(sc, (WIDTH // 2 - sc.get_width() // 2, HEIGHT // 2 - 15))

        hs = self.font_md.render(f"Best: {self.high_score:,}", True, YELLOW)
        self.screen.blit(hs, (WIDTH // 2 - hs.get_width() // 2, HEIGHT // 2 + 40))

        restart = self.font_md.render("SPACE / R  or  controller button  to play again", True, LIGHT_GRAY)
        self.screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 90))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key in (pygame.K_SPACE, pygame.K_r) and self.game_over:
                        self.reset_game()
                if event.type == pygame.JOYBUTTONDOWN and self.game_over:
                    self.reset_game()

            if not self.game_over:
                self.update()

            self.draw_field()
            for b in self.bumpers:
                b.draw(self.screen)
            self.left_flipper.draw(self.screen)
            self.right_flipper.draw(self.screen)
            for p in self.particles:
                p.draw(self.screen)
            for popup in self.popups:
                popup.draw(self.screen)
            self.ball.draw(self.screen)
            self.draw_hud()
            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
if __name__ == "__main__":
    Game().run()
