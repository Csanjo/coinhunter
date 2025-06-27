import pygame
import random
import asyncio

class CoinHunter:
    def __init__(self):
        pygame.init()

        self.load_images()

        self.keys = {'left': False, 'right': False, 'up': False, 'down': False}
        self.scale = self.images[1].get_width()

        self.new_game()
        self.height = len(self.map)
        self.width = len(self.map[0])

        self.game_over = False

        window_height = self.scale * self.height
        window_width = self.scale * self.width
        self.window = pygame.display.set_mode((window_width, window_height))
        self.restart_button_rect = pygame.Rect(0, 0, 200, 60)
        self.restart_button_rect.center = (self.window.get_width()//2, self.window.get_height() * 3 // 4)

        pygame.display.set_caption("Coin Hunter")

        # Jump variables
        self.is_jumping = False
        self.jump_speed = 12
        self.jump_velocity = 0
        self.gravity = 0.5
        self.ground_y = self.robot_y  # The "ground" position to land on after jump

        self.last_coin_spawn_time = pygame.time.get_ticks()  # current time in milliseconds
        self.coin_spawn_interval = 3000 

        # Monster
        self.monsters = [{
            'x': 5 * self.scale,
            'y': 6 * self.scale,
            'vel_x': 3,
            'vel_y': 3
        }]
        self.last_monster_spawn_time = pygame.time.get_ticks()
        self.monster_spawn_interval = 15000 

        # Font
        self.font = pygame.font.SysFont(None, 30)

        self.spawn_coins(3)
        self.survival_time = 0

        # Clock for frame timing
        self.clock = pygame.time.Clock()

    def load_images(self):
        self.images = []
        names = ["", "door", "monster", "robot", "coin"]
        for name in names:
            if name == "":
                self.images.append(None)
            else:
                self.images.append(pygame.image.load(name + ".png"))

    def new_game(self):
        self.coins = []
        self.coins_collected = 0
        self.start_time = pygame.time.get_ticks()
        self.map = [[5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
                    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1],
                    [1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1],
                    [1, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]

        for y in range(len(self.map)):
            for x in range(len(self.map[y])):
                if self.map[y][x] == 3:
                    self.robot_x = x * self.scale
                    self.robot_y = y * self.scale + 15
                    self.map[y][x] = 0

    def run_frame(self):
        # Process input/events
        self.check_events()

        if not self.game_over:
            self.update_robot()
            self.update_monsters()
            self.check_monster_robot_collision()
            self.draw_window()
        else:
            self.draw_game_over_screen()

        current_time = pygame.time.get_ticks()
        if current_time - self.last_coin_spawn_time >= self.coin_spawn_interval:
            self.spawn_coins(1)
            self.last_coin_spawn_time = current_time

        if not self.game_over:
            self.survival_time = (current_time - self.start_time) // 1000 

        if current_time - self.last_monster_spawn_time >= self.monster_spawn_interval:
            self.spawn_monster()
            self.last_monster_spawn_time = current_time

        # Cap framerate at 60 FPS
        self.clock.tick(60)


    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if not self.game_over:
                    # normal movement keys
                    if event.key == pygame.K_LEFT:
                        self.keys['left'] = True
                    elif event.key == pygame.K_RIGHT:
                        self.keys['right'] = True
                    elif event.key == pygame.K_SPACE:
                        if not self.is_jumping:
                            self.is_jumping = True
                            self.jump_velocity = -self.jump_speed
                    elif event.key == pygame.K_UP:
                        self.keys['up'] = True
                    elif event.key == pygame.K_DOWN:
                        self.keys['down'] = True
                else:
                    # maybe restart on space key
                    if event.key == pygame.K_SPACE:
                        self.restart_game()
            elif event.type == pygame.KEYUP and not self.game_over:
                if event.key == pygame.K_LEFT:
                    self.keys['left'] = False
                elif event.key == pygame.K_RIGHT:
                    self.keys['right'] = False
            elif event.type == pygame.MOUSEBUTTONDOWN and self.game_over:
                mouse_pos = event.pos
                # Check if restart button clicked
                if self.restart_button_rect.collidepoint(mouse_pos):
                    self.restart_game()

    def update_robot(self):
        speed = 3

        new_x = self.robot_x
        new_y = self.robot_y

        # Horizontal movement inputs
        if self.keys['left']:
            new_x -= speed
        if self.keys['right']:
            new_x += speed

        # Jumping physics
        if self.is_jumping:
            new_y += self.jump_velocity
            self.jump_velocity += self.gravity

            if new_y >= self.ground_y:
                new_y = self.ground_y
                self.is_jumping = False
                self.jump_velocity = 0

        # Collision detection
        # Check the 4 corners of the robot sprite at the new position
        corners = [
            (new_x, new_y),
            (new_x + self.scale - 1, new_y),
            (new_x, new_y + self.scale - 1),
            (new_x + self.scale - 1, new_y + self.scale - 1),
        ]

        for (corner_x, corner_y) in corners:
            tile_x = int(corner_x // self.scale)
            tile_y = int(corner_y // self.scale)

            # Check map bounds and if tile is a wall
            if (
                tile_x < 0 or tile_x >= self.width or
                tile_y < 0 or tile_y >= self.height or
                self.map[tile_y][tile_x] == 1  # wall tile
            ):
                # Collision detected, cancel movement horizontally and/or vertically
                # For simplicity, stop all movement this frame:
                return

        # No collision detected, update position
        self.robot_x = new_x
        self.robot_y = new_y

        tile_x = int(self.robot_x // self.scale)
        tile_y = int(self.robot_y // self.scale)

        # Collect coin if on one

        robot_rect = pygame.Rect(self.robot_x, self.robot_y, self.scale, self.scale)
        for coin in self.coins[:]:
            coin_x, coin_y = coin[0] * self.scale, coin[1] * self.scale
            coin_rect = pygame.Rect(coin_x, coin_y, self.scale, self.scale)
            if robot_rect.colliderect(coin_rect):
                self.coins.remove(coin)
                self.map[coin[1]][coin[0]] = 0  
                self.coins_collected += 1

    def update_monsters(self):
        for monster in self.monsters:
            new_x = monster['x'] + monster['vel_x']
            new_y = monster['y'] + monster['vel_y']

            collision_x = False
            collision_y = False

            corners = [
                (new_x, new_y),
                (new_x + self.scale - 1, new_y),
                (new_x, new_y + self.scale - 1),
                (new_x + self.scale - 1, new_y + self.scale - 1),
            ]

            for (corner_x, corner_y) in corners:
                tile_x = int(corner_x // self.scale)
                tile_y = int(corner_y // self.scale)

                if (tile_x < 0 or tile_x >= self.width or
                    tile_y < 0 or tile_y >= self.height or
                    self.map[tile_y][tile_x] == 1):
                    if tile_x < 0 or tile_x >= self.width or self.map[int(monster['y'] // self.scale)][tile_x] == 1:
                        collision_x = True
                    if tile_y < 0 or tile_y >= self.height or self.map[tile_y][int(monster['x'] // self.scale)] == 1:
                        collision_y = True

            if collision_x:
                monster['vel_x'] = -monster['vel_x']
            else:
                monster['x'] = new_x

            if collision_y:
                monster['vel_y'] = -monster['vel_y']
            else:
                monster['y'] = new_y



    def spawn_monster(self):
        attempts = 0
        while attempts < 100:
            x = random.randint(1, self.width - 2)
            y = random.randint(3, self.height - 2)  # Only rows inside the arena

            if (
                self.map[y][x] != 1 and  # not a wall
                (x, y) not in self.coins and
                (x, y) != (int(self.robot_x // self.scale), int(self.robot_y // self.scale)) and
                all((int(m['x'] // self.scale), int(m['y'] // self.scale)) != (x, y) for m in self.monsters)
            ):
                self.monsters.append({
                    'x': x * self.scale,
                    'y': y * self.scale,
                    'vel_x': random.choice([-3, 3]),
                    'vel_y': random.choice([-3, 3])
                })
                break
            attempts += 1


    def spawn_coins(self, count):
        coins_to_add = min(count, 3 - len(self.coins))
        if coins_to_add <= 0:
            return

        robot_tile_x = int(self.robot_x // self.scale)
        robot_tile_y = int(self.robot_y // self.scale)

        for _ in range(coins_to_add):
            attempts = 0
            while attempts < 100:
                x = random.randint(1, self.width - 2)
                y = random.randint(1, self.height - 2)

                occupied_by_monster = any(
                    (int(m['x'] // self.scale), int(m['y'] // self.scale)) == (x, y)
                    for m in self.monsters
                )

                if (
                    self.map[y][x] == 0 and
                    (x, y) not in self.coins and
                    (x, y) != (robot_tile_x, robot_tile_y) and
                    not occupied_by_monster
                ):
                    self.map[y][x] = 4
                    self.coins.append((x, y))
                    break
                attempts += 1

    def check_monster_robot_collision(self):
        robot_rect = pygame.Rect(self.robot_x, self.robot_y, self.scale, self.scale)

        for monster in self.monsters:
            margin = self.scale * 0.15
            monster_rect = pygame.Rect(
                monster['x'] + margin,
                monster['y'] + margin,
                self.scale * 0.6,
                self.scale * 0.6
            )

            if robot_rect.colliderect(monster_rect):
                self.game_over = True
                break


    def draw_game_over_screen(self):
        self.window.fill((50, 50, 50))  # dark background

        font_large = pygame.font.SysFont(None, 72)
        font_medium = pygame.font.SysFont(None, 48)
        font_small = pygame.font.SysFont(None, 36)

        # Game Over text
        text = font_large.render("Game Over", True, (255, 0, 0))
        text_rect = text.get_rect(center=(self.window.get_width()//2, self.window.get_height()//4))
        self.window.blit(text, text_rect)

        # Coins collected text
        coins_text = font_medium.render(f"Coins Collected: {self.coins_collected}", True, (255, 255, 255))
        coins_rect = coins_text.get_rect(center=(self.window.get_width()//2, self.window.get_height()//2 - 40))
        self.window.blit(coins_text, coins_rect)

        # Survival time text
        time_text = font_medium.render(f"Survival Time: {self.survival_time}s", True, (255, 255, 255))
        time_rect = time_text.get_rect(center=(self.window.get_width()//2, self.window.get_height()//2 + 10))
        self.window.blit(time_text, time_rect)

        # Restart button
        pygame.draw.rect(self.window, (200, 200, 200), self.restart_button_rect)

        button_text = font_small.render("Restart", True, (0, 0, 0))
        button_text_rect = button_text.get_rect(center=self.restart_button_rect.center)
        self.window.blit(button_text, button_text_rect)


        pygame.display.flip()


    def restart_game(self):
        self.new_game()
        self.spawn_coins(3)
        self.game_over = False
        self.monsters = [{
            'x': 5 * self.scale,
            'y': 6 * self.scale,
            'vel_x': 3,
            'vel_y': 3
        }]
        self.last_monster_spawn_time = pygame.time.get_ticks()
        self.keys = {'left': False, 'right': False, 'up': False, 'down': False}
        self.is_jumping = False
        self.jump_velocity = 0
        self.coins_collected = 0
        self.start_time = pygame.time.get_ticks()

    def draw_window(self):
        self.window.fill((173, 216, 230))  # background

        # Draw walls and other tiles
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x] == 1:
                    pygame.draw.rect(self.window, (139, 69, 19), (x*self.scale, y*self.scale, self.scale, self.scale))
        
        # Draw coins
        for coin in self.coins:
            pixel_x = coin[0] * self.scale
            pixel_y = coin[1] * self.scale
            self.window.blit(self.images[4], (pixel_x, pixel_y))
        
        # Draw robot
        self.window.blit(self.images[3], (self.robot_x, self.robot_y))

        # Draw monster (fixed typo)
        for monster in self.monsters:
            self.window.blit(self.images[2], (monster['x'], monster['y']))

        # Draw coin count
        coin_text = self.font.render(f"Coins: {self.coins_collected}", True, (50, 50, 50))
        self.window.blit(coin_text, (10, 10))

        # Draw survival time
        time_text = self.font.render(f"Time: {self.survival_time}s", True, (50, 50, 50))
        self.window.blit(time_text, (10, 40))

        pygame.display.flip()


async def main():
    game = CoinHunter()
    while True:
        game.run_frame()
        await asyncio.sleep(0)  # yield control to event loop


if __name__ == "__main__":
    asyncio.run(main())
