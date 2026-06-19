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
        pygame.display.set_caption("Legal Literacy Game")
        self.clock = pygame.time.Clock()
        
        # Шрифты
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 40)
        self.small_font = pygame.font.SysFont("Arial", 18)

        # Состояния игры: 'menu', 'settings', 'edit_ui', 'registration', 'game', 'pause', 'game_over', 'victory'
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
        self.quest_state = 'wait' # 'wait', 'find_item', 'ask_suspect', 'escort'
        self.item_picked_up = False
        self.dialogue_line_idx = 0
        self.active_cutscene = None # Переменная для хранения списков строк кат-сцен
        self.show_choice = False

        # Инициализация интерфейса тачей
        self.ui = TouchInterface()

        # Загрузка ассетов (с защитой от вылета, если папка assets еще пуста)
        self.load_assets()

    def load_assets(self):
        self.assets = {}
        # Список необходимых картинок
        names = ['player', 'boy_1', 'boy_2', 'spray', 'phone', 'shocker']
        for name in names:
            path = f"assets/{name}.png"
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                if 'player' in name or 'boy' in name:
                    img = pygame.transform.scale(img, (PLAYER_W, PLAYER_H))
                else:
                    img = pygame.transform.scale(img, (40, 40))
                self.assets[name] = img
            else:
                # Если файла нет, временно создаем цветную заглушку, чтобы игра запустилась
                surf = pygame.Surface((PLAYER_W, PLAYER_H) if 'player' in name or 'boy' in name else (40, 40))
                surf.fill(RED if 'spray' in name else BLUE)
                self.assets[name] = surf

    def get_text(self, key):
        return translations[self.lang].get(key, key)

    def run(self):
        while True:
            dt = self.clock.tick(60)
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Перехват ввода имени в режиме регистрации
            if self.state == 'registration' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif event.key == pygame.K_RETURN and len(self.player_name) > 2:
                    self.state = 'game'
                else:
                    if len(self.player_name) < 20 and event.unicode.isalnum() or event.unicode == ' ':
                        self.player_name += event.unicode

            # Обработка тач-интерфейса (джойстик и кнопка действия)
            dx, dy, action = self.ui.handle_event(event)
            
            if self.state == 'game' and not self.active_cutscene and not self.show_choice:
                # Движение игрока от джойстика
                self.player_x += dx * player_speed
                # Ограничение по границам карты школы
                self.player_x = max(50, min(self.player_x, MAP_W - 150))
                
                if action:
                    self.process_game_action()
            
            elif (self.state == 'game' or self.state == 'edit_ui') and action:
                # Если идет кат-сцена или диалог, кнопка действия мотает текст дальше
                self.process_ui_action()

            # Обработка обычных кликов по кнопкам менюшек
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.process_menu_clicks(event.pos)

    def process_game_action(self):
        """Логика кнопки действия (Вход в двери, допрос, сбор улик)"""
        t = translations[self.lang]
        current_case = t['cases'][self.current_case_idx] if self.current_case_idx < len(t['cases']) else None

        # Проверка дверей на 1 этаже
        if self.player_floor == 1:
            # Вход в школу
            if abs(self.player_x - school_door_x) < 50:
                self.player_floor = 2 # Переносимся внутрь на 2 этаж
                self.player_x = 300
                return
            # Вход в полицию
            if abs(self.player_x - police_door_x) < 50:
                self.player_floor = 'police'
                self.player_x = 100
                return

        # Проверка лестниц внутри школы
        if self.player_floor == 2 and abs(self.player_x - stairs_up_x) < 50:
            self.player_floor = 3
            self.player_x = stairs_up_x
            return
        if self.player_floor == 3 and abs(self.player_x - stairs_down_x) < 50:
            self.player_floor = 2
            self.player_x = stairs_down_x
            return
            
        # Выход из школы или полиции на улицу (1 этаж)
        if self.player_floor == 2 and abs(self.player_x - 300) < 50: # Выход из школы
            self.player_floor = 1
            self.player_x = school_door_x
            return
        if self.player_floor == 'police' and abs(self.player_x - 100) < 50:
            self.player_floor = 1
            self.player_x = police_door_x
            return

        # Логика поднятия улик
        if self.quest_state == 'find_item' and current_case:
            if self.player_floor == current_case['floor'] and abs(self.player_x - current_case['ix']) < 60:
                self.item_picked_up = True
                self.quest_state = 'ask_suspect'
                return

        # Логика разговора с подозреваемым
        if self.quest_state == 'ask_suspect' and current_case:
            if self.player_floor == current_case['floor'] and abs(self.player_x - (current_case['ix'] + 150)) < 80:
                self.active_cutscene = current_case['dial']
                self.dialogue_line_idx = 0
                self.show_choice = True # Выводим меню выбора правонарушения по окончании диалога
                return

    def process_ui_action(self):
        """Продвижение текстов по клику на кнопку действия"""
        if self.active_cutscene:
            self.dialogue_line_idx += 1
            if self.dialogue_line_idx >= len(self.active_cutscene):
                self.active_cutscene = None
                if self.show_choice:
                    pass # Оставляем окно выбора открытым
                elif self.quest_state == 'escort':
                    # Сцена у завуча завершена, закрываем кейс
                    self.current_case_idx += 1
                    t = translations[self.lang]
                    if self.current_case_idx >= len(t['cases']):
                        self.state = 'victory'
                    else:
                        self.quest_state = 'wait'
                        self.item_picked_up = False

    def process_menu_clicks(self, pos):
        mx, my = pos
        # Кнопки Главного Меню
        if self.state == 'menu':
            if pygame.Rect(300, 200, 200, 50).collidepoint(mx, my):
                self.state = 'registration'
            elif pygame.Rect(300, 280, 200, 50).collidepoint(mx, my):
                self.state = 'settings'
            elif pygame.Rect(300, 360, 200, 50).collidepoint(mx, my):
                pygame.quit()
                sys.exit()

        # Кнопки Настроек
        elif self.state == 'settings':
            if pygame.Rect(300, 200, 200, 50).collidepoint(mx, my):
                self.lang = 'kk' if self.lang == 'ru' else 'ru'
            elif pygame.Rect(300, 280, 200, 50).collidepoint(mx, my):
                self.state = 'edit_ui'
                self.ui.edit_mode = True # Включаем кастомизацию кнопок!
            elif pygame.Rect(300, 360, 200, 50).collidepoint(mx, my):
                self.state = 'menu'

        # Выход из режима кастомизации управления
        elif self.state == 'edit_ui':
            # Маленькая кнопка "Сохранить" вверху экрана
            if pygame.Rect(20, 20, 150, 40).collidepoint(mx, my):
                self.ui.edit_mode = False
                self.state = 'settings'

        # Выбор ответа в кейсе правосудия
        elif self.state == 'game' and self.show_choice:
            t = translations[self.lang]
            current_case = t['cases'][self.current_case_idx]
            # Три варианта ответа
            for i in range(3):
                if pygame.Rect(100, 350 + i*55, 600, 45).collidepoint(mx, my):
                    if i == current_case['choice']['cor']:
                        self.score += 25
                        self.active_cutscene = current_case['ht'] # Запуск финального разбора у Завуча
                        self.quest_state = 'escort'
                    else:
                        self.lives -= 1
                        self.active_cutscene = current_case['choice']['fail']
                        if self.lives <= 0:
                            self.state = 'game_over'
                    self.dialogue_line_idx = 0
                    self.show_choice = False

    def update(self):
        # Если мы просто ждем звонка от завуча, запускаем новый кейс
        if self.state == 'game' and self.quest_state == 'wait':
            t = translations[self.lang]
            if self.current_case_idx < len(t['cases']):
                self.quest_state = 'find_item'
                self.active_cutscene = t['cases'][self.current_case_idx]['call']
                self.dialogue_line_idx = 0

    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        if self.state == 'menu':
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
        self.draw_text_centered("LEGAL LITERACY GAME", self.title_font, YELLOW, 80)
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
        # Поле ввода текста
        input_rect = pygame.Rect(200, 330, 400, 50)
        pygame.draw.rect(self.screen, WHITE, input_rect, border_radius=5)
        pygame.draw.rect(self.screen, BLUE, input_rect, 2, border_radius=5)
        
        name_surf = self.font.render(self.player_name, True, BLACK)
        self.screen.blit(name_surf, (input_rect.x + 10, input_rect.y + 10))

    def draw_game_world(self):
        """Отрисовка локаций в зависимости от этажа"""
        if self.player_floor == 1: # Улица Астаны
            # Дорога
            pygame.draw.rect(self.screen, ROAD_COLOR, (0, 450, WIDTH, 150))
            # Школа Гимназия №83
            pygame.draw.rect(self.screen, WOOD, (SCHOOL_X, SCHOOL_Y + 150, SCHOOL_W, SCHOOL_H))
            pygame.draw.rect(self.screen, DARK_GRAY, (school_door_x - 25, 270, 50, 80)) # Дверь
            # Полиция
            pygame.draw.rect(self.screen, POLICE_COLOR, (POLICE_X, POLICE_Y, POLICE_W, POLICE_H - 100))
            
        elif self.player_floor in [2, 3]: # Внутри школы (Коридоры)
            self.screen.fill(GRAY)
            pygame.draw.rect(self.screen, DARK_GRAY, (0, 500, WIDTH, 100)) # Пол
            # Отрисовка лестниц
            pygame.draw.rect(self.screen, WHITE, (stairs_up_x - 1000, 400, 60, 100)) 
            
            # Если в текущем кейсе игрок находится на нужном этаже, рисуем подозреваемого и улику
            t = translations[self.lang]
            if self.current_case_idx < len(t['cases']):
                case = t['cases'][self.current_case_idx]
                if case['floor'] == self.player_floor:
                    # Подозреваемый ученик
                    self.screen.blit(self.assets[case['sprite']], (case['ix'] + 150 - self.player_x + WIDTH//2, 400))
                    # Улика на полу (если еще не подобрана)
                    if not self.item_picked_up and self.quest_state == 'find_item':
                        self.screen.blit(self.assets[case['item']], (case['ix'] - self.player_x + WIDTH//2, 460))

        elif self.player_floor == 'police':
            self.screen.fill(DARK_BLUE)
            pygame.draw.rect(self.screen, DARK_GRAY, (0, 500, WIDTH, 100))

        # Отрисовка игрока (Детектива) по центру экрана (камера привязана к нему)
        screen_player_x = WIDTH // 2 if self.player_floor in [2, 3] else self.player_x
        self.screen.blit(self.assets['player'], (screen_player_x, 400))

    def draw_hud_and_dialogues(self):
        # Отрисовка жизней и очков вверху экрана
        hud_text = f"{self.get_text('lives_text')}{self.lives}  |  {self.get_text('score_text')}{self.score}"
        hud_surf = self.font.render(hud_text, True, YELLOW)
        self.screen.blit(hud_surf, (20, 20))
        
        floor_text = f"{self.get_text('floor')}: {self.player_floor}"
        self.screen.blit(self.font.render(floor_text, True, WHITE), (WIDTH - 150, 20))

        # Отрисовка всплывающего диалогового окна/кат-сцен
        if self.active_cutscene and self.dialogue_line_idx < len(self.active_cutscene):
            box_rect = pygame.Rect(50, HEIGHT - 250, WIDTH - 100, 100)
            pygame.draw.rect(self.screen, BLACK, box_rect, border_radius=10)
            pygame.draw.rect(self.screen, WHITE, box_rect, 3, border_radius=10)
            
            line = self.active_cutscene[self.dialogue_line_idx].format(name=self.player_name)
            surf = self.font.render(line, True, WHITE)
            self.screen.blit(surf, (box_rect.x + 20, box_rect.y + 20))
            
            click_surf = self.small_font.render(self.get_text("click"), True, YELLOW)
            self.screen.blit(click_surf, (box_rect.right - 100, box_rect.bottom - 25))

        # Отрисовка интерактивного меню выбора статьи (Юридический тест)
        if self.show_choice:
            t = translations[self.lang]
            case = t['cases'][self.current_case_idx]
            
            # Задний фон для карточки теста
            pygame.draw.rect(self.screen, DARK_GRAY, (50, 280, WIDTH - 100, 280), border_radius=15)
            q_surf = self.font.render(case['choice']['q'], True, YELLOW)
            self.screen.blit(q_surf, (80, 295))
            
            for i, opt in enumerate(case['choice']['opt']):
                btn_rect = pygame.Rect(100, 350 + i*55, 600, 45)
                draw_button(self.screen, opt, self.small_font, btn_rect, BLUE, WHITE)

    def draw_text_centered(self, text, font, color, y):
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(WIDTH // 2, y))
        self.screen.blit(surf, rect)

if __name__ == "__main__":
    game = Game()
    game.run()
