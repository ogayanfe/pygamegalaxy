import pygame
import random
from abc import ABC, abstractmethod
from pygame.locals import KEYDOWN, K_ESCAPE, QUIT, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_SPACE, RLEACCEL
import os

pygame.init()
pygame.mixer.init()
pygame.font.init()

pygame.mixer.music.load("battle-march-action-loop-6935.mp3")
pygame.mixer.music.set_volume(.5)
pygame.mixer.music.play(-1)

WIDTH: int = 1000
HEIGHT: int = 600
BG_COLOR: tuple[int, int, int] = (2, 3, 14)
ADD_NEW_ENEMY: int = pygame.USEREVENT + 1
ADD_PLAYER_BULLET: int = ADD_NEW_ENEMY + 1

screen = pygame.display.set_mode((WIDTH, HEIGHT))
bg_image = pygame.transform.scale(
    pygame.image.load("galaxy.png"), (WIDTH, HEIGHT))
screen.blit(bg_image, (0, 0))


# Sprite Groups
enemies = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()

# Sprite images
enemy_image = pygame.image.load("Gepard.png")
player_image = pygame.image.load("stateczek.png")

# Fire a had enemy event every 5 seconds
pygame.time.set_timer(ADD_NEW_ENEMY, 500)
pygame.time.set_timer(ADD_PLAYER_BULLET, 300)

clock = pygame.time.Clock()

system_fonts = pygame.font.get_fonts()


def get_random_bullet_surface():
    file_index = f'{random.randint(1, 66):2}'.replace(" ", "0") + ".png"
    random_file_path = os.path.join("bullets", file_index)
    image = pygame.image.load(random_file_path)
    image = pygame.transform.scale(image, (20, 20))
    return pygame.transform.rotate(image, -90)


def get_font_surface(text: str, color: tuple[int, int, int], font_size: int):
    font = pygame.font.SysFont(system_fonts,  font_size)
    img = font.render(text, False, color)
    return img


class GameProp(pygame.sprite.Sprite, ABC):
    def __init__(self, pos: tuple[int, int], velocity: int):
        super().__init__()
        self.surf = pygame.Surface((75, 25))
        self.rect = self.surf.get_rect(center=pos)
        self.vel = velocity
        self.xvel = None
        self.yvel = None
        self.padding = 10

    def move(self, left: bool = False, right: bool = False, up: bool = False, down: bool = False):
        xvel = self.xvel if self.xvel else self.vel
        yvel = self.yvel if self.yvel else self.vel

        if right and self.rect.right < WIDTH - self.padding:
            self.rect.right += xvel

        if left and self.rect.left > 0 + self.padding:
            self.rect.left -= xvel

        if up and self.rect.top > 0 + self.padding:
            self.rect.top -= yvel

        if down and self.rect.bottom < HEIGHT - self.padding:
            self.rect.bottom += yvel

    def x_out_of_bounds(self) -> bool:
        xvel = self.xvel if self.xvel else self.vel

        if self.rect.right + xvel > WIDTH - self.padding:
            return True
        if self.rect.left - xvel < 0 + self.padding:
            return True
        return False

    def check_top(self, yvel) -> bool:
        return self.rect.bottom + yvel > HEIGHT - self.padding

    def check_bottom(self, yvel) -> bool:
        return self.rect.top - yvel < self.padding

    def y_out_of_bounds(self) -> bool:
        yvel = self.yvel if self.yvel else self.vel
        return self.check_top(yvel) or self.check_bottom(yvel)

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


class Bullet(GameProp):
    def __init__(self, pos: tuple[int, int],  up: bool = True):
        super().__init__(pos, velocity=10)
        self.up = up
        self.surf = get_random_bullet_surface()
        self.padding = 0
        self.sound = None

    def update(self, *_):
        if self.y_out_of_bounds():
            self.kill()
        self.move(up=self.up, down=not self.up)

    def set_surfaces(self):
        pass


class Character(GameProp):

    is_enemy: bool

    def shoot(self, up=True):
        pos = (self.rect.centerx, self.rect.top)
        new_bullet = Bullet(pos=pos, up=up)
        all_sprites.add(new_bullet)
        if self.is_enemy:
            enemy_bullets.add(new_bullet)
            return
        player_bullets.add(new_bullet)


class Player(Character):

    is_enemy = False

    def __init__(self, pos: tuple[int, int], ):
        super().__init__(pos, velocity=10)
        self.surf = pygame.transform.scale(player_image, (60, 60))
        self.surf.set_colorkey((0, 0, 0), RLEACCEL)
        self.rect = self.surf.get_rect(center=pos)
        self.no_of_bullets = 1

    def update(self, pressedKeys):
        if pygame.sprite.spritecollideany(self, enemies):
            self.kill()
            return
        if pygame.sprite.spritecollideany(self, enemy_bullets):
            self.kill()
            return

        self.move(
            left=pressedKeys[K_LEFT],
            right=pressedKeys[K_RIGHT],
            up=pressedKeys[K_UP],
            down=pressedKeys[K_DOWN]
        )

        if pressedKeys[K_SPACE] and self.no_of_bullets > 0:
            self.shoot()
            self.no_of_bullets -= 1
            get_random_bullet_surface()

    def add_bullet(self):
        if self.no_of_bullets >= 10:
            return
        self.no_of_bullets += 1


class Enemy(Character):

    is_enemy = True
    kill_count = 0

    def __init__(self):
        random_pos = (random.randint(30, HEIGHT), 30)
        super().__init__(pos=random_pos, velocity=6)
        self.facing: bool = random.choice((True, False))
        self.surf = pygame.transform.scale(enemy_image, (50, 50))
        self.rect = self.surf.get_rect(center=random_pos)
        self.yvel = 1
        self.padding = 0

    @classmethod
    def add_kill(cls):
        cls.kill_count += 1

    def check_top(self, *_) -> bool:
        return False

    def update(self, _):
        randomNum = random.random()
        if self.x_out_of_bounds():
            self.facing = not self.facing
        if self.y_out_of_bounds():
            self.kill()
            return
        if pygame.sprite.spritecollideany(self, player_bullets):
            self.add_kill()
            self.kill()
            cleanup(pygame.sprite.spritecollideany(self, player_bullets))

            return
        if randomNum >= .99:
            self.shoot(up=False)
        self.move(left=self.facing, right=not self.facing, down=True)


player: Player = Player((WIDTH // 2, HEIGHT - 20))
all_sprites.add(player)

running: bool = True


def cleanup(p: GameProp | None):
    """
    Cleanups any prop object that collides with any group 

    Args:
        p (Bullet | None): A GameProp object 
    """
    if p is not None:
        p.kill()


while running:
    clock.tick(20)
    screen.blit(bg_image, (0, 0))

    for event in pygame.event.get():
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                running = False

        elif event.type == QUIT:
            running = False

        if event.type == ADD_NEW_ENEMY:
            new_enemy = Enemy()
            all_sprites.add(new_enemy)
            enemies.add(new_enemy)

        if event.type == ADD_PLAYER_BULLET:
            player.add_bullet()

    for entity in all_sprites:
        entity.update(pygame.key.get_pressed())
        screen.blit(entity.surf, entity.rect)

    if pygame.sprite.spritecollideany(player, enemies):
        player.kill()

    bullet_text = f'Bullet Count: {player.no_of_bullets}'
    screen.blit(get_font_surface(
        bullet_text, (255, 255, 255), 20), (10, HEIGHT - 40))

    score = Enemy.kill_count
    score_surface = get_font_surface(f'SCORE: {score}', (225, 255, 255), 30)

    screen.blit(score_surface, ((WIDTH / 2) -
                score_surface.get_width() / 2, 50))
    pygame.display.update()
