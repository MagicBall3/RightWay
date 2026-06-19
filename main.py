# main.py
import pygame
import sys
import os
from src.config import *
from src.ui import TouchInterface, draw_button

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("RightWay")
        self.clock = pygame.time.Clock()
        
        # Шрифты
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 40)
        self.small_font = pygame.font.SysFont("Arial", 18)

        # Состояния игры
        self.state = 'menu'
        self.lang = 'ru'
        
        # Данные игрока
        self.player_name = ""
        self.player_x = 100
        self.player_y = 450
        self.player_floor = 1
        self.score = 0
        self.lives = 3
        
        # Логика квестов и кейсов
        self.current_case_idx = 0
        self.quest_state = 'wait'  # 'wait', 'find_item', 'ask_suspect', 'escort'
        self.item_picked_up = False
        self.dialogue_line_idx = 0
        self.active_cutscene = None
        self.show_choice = False

        # Инициализация интерфейса тачей
        self.ui = TouchInterface()

        # Полная загрузка твоих ассетов из видео
        self.load_assets()

    def load_assets(self):
        self.assets = {}
        
        # 1. Текстуры окружения и зданий
        bg_elements = {
            'house': (HOUSE_W, HOUSE_H),
            'police': (POLICE_W, POLICE_H),
            'school': (SCHOOL_W, SCHOOL_H),
            'road': (WIDTH, 150),
            'tile': (WIDTH, HEIGHT),
            'wood': (WIDTH, 100),
            'splash': (WIDTH, HEIGHT)
        }
        
        # 2. Персонажи и предметы (улики)
        sprites_and_items = {
            'player': (PLAYER_W, PLAYER_H),
            'npc_boy_1': (PLAYER_W, PLAYER_H),
            'npc_boy_2': (PLAYER_W, PLAYER_H),
            'npc_girl_1': (PLAYER_W, PLAYER_H),
            'npc_girl_2': (PLAYER_W, PLAYER_H),
            'npc_director': (PLAYER_W, PLAYER_H),
            'npc_head_teacher': (PLAYER_W, PLAYER_H),
            'npc_teacher_f': (PLAYER_W, PLAYER_H),
            'npc_guard': (PLAYER_W, PLAYER_H),
            'npc_worker': (PLAYER_W, PLAYER_H),
            'item_phone': (40, 40),
            'item_shocker': (40, 40),
            'item_spray': (40, 40)
        }

        # Функция безопасной загрузки с автоматическим изменением размера под хитбоксы
        def fetch_img(name, size, folder="assets"):
            # Проверяем оба расширения, так как на видео есть и png, и jpg
            for ext in ['.png', '.jpg']:
                path = f"{folder}/{name}{ext}"
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    return pygame.transform.scale(img, size)
            
            # Если файла нет, создаем цветной квадрат-заглушку
            surf = pygame.Surface(size)
            surf.fill((100, 100, 100))
            return surf

        # Загружаем всё в словарь self.assets
        for name, size in bg_elements.items():
            self.assets[name] = fetch_img(name, size)
            
        for name, size in sprites_and_items.items():
            self.assets[name] = fetch_img(name, size)

    def get_text(self, key):
        return translations[self.lang].get(key, key)

    def run(self):
        while True:
            self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if self.state == 'registration' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif event.key == pygame.K_RETURN and len(self.player_name) > 2:
                    self.state = 'game'
                else:
                    if len(self.player_name) < 20 and (event.unicode.isalnum() or event.unicode == ' '):
                        self.player_name += event.unicode

            dx, dy, action = self.ui.handle_event(event)
            
            if self.state == 'game' and not self.active_cutscene and not self.show_choice:
                self.player_x += dx * player_speed
                self.player_x = max(50, min(self.player_x, MAP_W - 150))
                
                if action:
                    self.process_game_action()
            
            elif (self.state == 'game' or self.state == 'edit_ui') and action:
                self.process_ui_action()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.process_menu_clicks(event.pos)

    def process_game_action(self):
        t = translations[self.lang]
        current_case = t['cases'][self.current_case_idx] if self.current_case_idx < len(t['cases']) else None

        if self.player_floor == 1:
            if abs(self.player_x - school_door_x) < 60:
                self.player_floor = 2
                self.player_x = 300
                return
            if abs(self.player_x - police_door_x) < 60:
                self.player_floor = 'police'
                self.player_x = 100
                return

        if self.player_floor == 2 and abs(self.player_x - stairs_up_x) < 60:
            self.player_floor = 3
            self.player_x = stairs_up_x
            return
        if self.player_floor == 3 and abs(self.player_x - stairs_down_x) < 60:
            self.player_floor = 2
            self.player_x = stairs_down_x
            return
            
        if self.player_floor == 2 and abs(self.player_x - 300) < 60:
            self.player_floor = 1
            self.player_x = school_door_x
            return
        if self.player_floor == 'police' and abs(self.player_x - 100) < 60:
            self.player_floor = 1
            self.player_x = police_door_x
            return

        if self.quest_state == 'find_item' and current_case:
            if self.player_floor == current_case['floor'] and abs(self.player_x - current_case['ix']) < 70:
                self.item_picked_up = True
                self.quest_state = 'ask_suspect'
                return

        if self.quest_state == 'ask_suspect' and current_case:
            # Префиксы к именам файлов из видео: npc_boy_1 или npc_boy_2
            sprite_asset_name = f"npc_{current_case['sprite']}"
            if self.player_floor == current_case['floor'] and abs(self.player_x - (current_case['ix'] + 150)) < 90:
                self.active_cutscene = current_case['dial']
                self.dialogue_line_idx = 0
                self.show_choice = True
                return

    def process_ui_action(self):
        if self.active_cutscene:
            self.dialogue_line_idx += 1
            if self.dialogue_line_idx >= len(self.active_cutscene):
                self.active_cutscene = None
                if self.show_choice:
                    pass
                elif self.quest_state == 'escort':
                    self.current_case_idx += 1
                    t = translations[self.lang]
                    if self.current_case_idx >= len(t['cases']):
                        self.state = 'victory'
                    else:
                        self.quest_state = 'wait'
                        self.item_picked_up = False

    def process_menu_clicks(self, pos):
        mx, my = pos
        if self.state == 'menu':
            if pygame.Rect(300, 200, 200, 50).collidepoint(mx, my):
                self.state = 'registration'
            elif pygame.Rect(300, 280, 200, 50).collidepoint(mx, my):
                self.state = 'settings'
            elif pygame.Rect(300, 360, 200, 50).collidepoint(mx, my):
                pygame.quit()
                sys.exit()

        elif self.state == 'settings':
            if pygame.Rect(300, 200, 200, 50).collidepoint(mx, my):
                self.lang = 'kk' if self.lang == 'ru' else 'ru'
            elif pygame.Rect(300, 280, 200, 50).collidepoint(mx, my):
                self.state = 'edit_ui'
                self.ui.edit_mode = True
            elif pygame.Rect(300, 360, 200, 50).collidepoint(mx, my):
                self.state = 'menu'

        elif self.state == 'edit_ui':
            if pygame.Rect(20, 20, 150, 40).collidepoint(mx, my):
                self.ui.edit_mode = False
                self.state = 'settings'

        elif self.state == 'game' and self.show_choice:
            t = translations[self.lang]
            current_case = t['cases'][self.current_case_idx]
            for i in range(3):
                if pygame.Rect(100, 350 + i*55, 600, 45).collidepoint(mx, my):
                    if i == current_case['choice']['cor']:
                        self.score += 25
                        self.active_cutscene = current_case['ht']
                        self.quest_state = 'escort'
                    else:
                        self.lives -= 1
                        self.active_cutscene = current_case['choice']['fail']
                        if self.lives <= 0:
                            self.state = 'game_over'
                    self.dialogue_line_idx = 0
                    self.show_choice = False

    def update(self):
        if self.state == 'game' and self.quest_state == 'wait':
            t = translations[self.lang]
            if self.current_case_idx < len(t['cases']):
                self.quest_state = 'find_item'
                self.active_cutscene = t['cases'][self.current_case_idx]['call']
                self.dialogue_line_idx = 0

    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        if self.state == 'menu':
            # Отрисовка фонового сплеша для меню
            self.screen.blit(self.assets['splash'], (0, 0))
            self.draw_menu()
        elif self.state == 'settings':
            self.draw_settings()
        elif self.state == 'edit_ui':
            self.ui.draw(self.screen)
            draw_button(self.screen, "<- Save", self.font, pygame.Rect(20, 20, 150, 40), GREEN, WHITE)
        elif self.state == 'registration':
            self.draw_registration()
        elif self.state == 'game':
            self.draw_game_world()
            self.ui.draw(self.screen)
            self.draw_hud_and_dialogues()
        elif self.state == 'game_over':
            self.draw_text_centered(self.get_text("game_over"), self.title_font, RED, HEIGHT//2 - 50)
        elif self.state == 'victory':
            self.screen.fill(GREEN)
            self.draw_text_centered(self.get_text("victory"), self.title_font, WHITE, HEIGHT//2 - 50)

        pygame.display.flip()

    def draw_menu(self):
        self.draw_text_centered("RIGHTWAY", self.title_font, YELLOW, 80)
        draw_button(self.screen, self.get_text("start"), self.font, pygame.Rect(300, 200, 200, 50), BLUE, WHITE)
        draw_button(self.screen, self.get_text("settings"), self.font, pygame.Rect(300, 280, 200, 50), GRAY, BLACK)
        draw_button(self.screen, self.get_text("exit"), self.font, pygame.Rect(300, 360, 200, 50), RED, WHITE)

    def draw_settings(self):
        self.draw_text_centered(self.get_text("settings_title"), self.title_font, WHITE, 80)
        draw_button(self.screen, self.get_text("lang"), self.font, pygame.Rect(300, 200, 200, 50), BLUE, WHITE)
        draw_button(self.screen, "Управление", self.font, pygame.Rect(300, 280, 200, 50), YELLOW, BLACK)
        draw_button(self.screen, self.get_text("back"), self.font, pygame.Rect(300, 360, 200, 50), RED, WHITE)

    def draw_registration(self):
        self.draw_text_centered(self.get_text("reg_title"), self.title_font, WHITE, 80)
        self.draw_text_centered(self.get_text("city"), self.font, GRAY, 160)
        self.draw_text_centered(self.get_text("school"), self.font, GRAY, 200)
        self.draw_text_centered(self.get_text("enter_name"), self.font, YELLOW, 280)
        
        input_rect = pygame.Rect(200, 330, 400, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLUE, input_rect, 2, border_radius=5)
        
        name_surf = self.font.render(self.player_name, True, BLACK)
        self.screen.blit(name_surf, (input_rect.x + 10, input_rect.y + 10))

    def draw_game_world(self):
        if self.player_floor == 1:
            # Отрисовка неба/города на заднем фоне через плитку tile
            self.screen.blit(self.assets['tile'], (0, 0))
            # Отрисовка дороги из твоего файла road.jpg
            self.screen.blit(self.assets['road'], (0, 450))
            
            # Здания из твоих картинок
            self.screen.blit(self.assets['school'], (SCHOOL_X, 150))
            self.screen.blit(self.assets['house'], (HOUSE_X, 250))
            self.screen.blit(self.assets['police'], (POLICE_X, 200))
            
            # Охранник у дверей школы
            self.screen.blit(self.assets['npc_guard'], (school_door_x + 50, 350))
            
        elif self.player_floor in [2, 3]:
            # Внутренние стены школы — заменяем на текстуру дерева wood.jpg
            self.screen.blit(self.assets['tile'], (0, 0))
            self.screen.blit(self.assets['wood'], (0, 500)) # Деревянный пол
            
            # Отрисовка кабинета завуча / директора, если идет сцена сопровождения
            if self.quest_state == 'escort':
                self.screen.blit(self.assets['npc_head_teacher'], (200, 400))
                self.screen.blit(self.assets['npc_director'], (100, 400))

            t = translations[self.lang]
            if self.current_case_idx < len(t['cases']):
                case = t['cases'][self.current_case_idx]
                if case['floor'] == self.player_floor:
                    # Корректный спрайт мальчика из видео (npc_boy_1 или npc_boy_2)
                    boy_asset = f"npc_{case['sprite']}"
                    self.screen.blit(self.assets[boy_asset], (case['ix'] + 150 - self.player_x + WIDTH//2, 400))
                    
                    if not self.item_picked_up and self.quest_state == 'find_item':
                        # Корректная улика из видео (item_spray, item_phone, item_shocker)
                        item_asset = f"item_{case['item']}"
                        self.screen.blit(self.assets[item_asset], (case['ix'] - self.player_x + WIDTH//2, 460))

        elif self.player_floor == 'police':
            self.screen.fill(DARK_BLUE)
            self.screen.blit(self.assets['wood'], (0, 500))
            self.screen.blit(self.assets['npc_worker'], (300, 400))

        # Отрисовка игрока (Детектива)
        screen_player_x = WIDTH // 2 if self.player_floor in [2, 3] else self.player_x
        self.screen.blit(self.assets['player'], (screen_player_x, 400))

    def draw_hud_and_dialogues(self):
        hud_text = f"{self.get_text('lives_text')}{self.lives}  |  {self.get_text('score_text')}{self.score}"
        self.screen.blit(self.font.render(hud_text, True, YELLOW), (20, 20))
        
        floor_text = f"{self.get_text('floor')}: {self.player_floor}"
        self.screen.blit(self.font.render(floor_text, True, WHITE), (WIDTH - 150, 20))

        if self.active_cutscene and self.dialogue_line_idx < len(self.active_cutscene):
            box_rect = pygame.Rect(50, HEIGHT - 250, WIDTH - 100, 100)
            pygame.draw.rect(self.screen, BLACK, box_rect, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, box_rect, 3, border_radius=10)
            
            line = self.active_cutscene[self.dialogue_line_idx].format(name=self.player_name)
            self.screen.blit(self.font.render(line, True, WHITE), (box_rect.x + 20, box_rect.y + 20))
            self.screen.blit(self.small_font.render(self.get_text("click"), True, YELLOW), (box_rect.right - 100, box_rect.bottom - 25))

        if self.show_choice:
            t = translations[self.lang]
            case = t['cases'][self.current_case_idx]
            pygame.draw.rect(self.screen, DARK_GRAY, (50, 280, WIDTH - 100, 280), border_radius=15)
            self.screen.blit(self.font.render(case['choice']['q'], True, YELLOW), (80, 295))
            for i, opt in enumerate(case['choice']['opt']):
                draw_button(self.screen, opt, self.small_font, pygame.Rect(100, 350 + i*55, 600, 45), BLUE, WHITE)

    def draw_text_centered(self, text, font, color, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))

if __name__ == "__main__":
    game = Game()
    game.run()
