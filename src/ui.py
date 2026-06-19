# src/ui.py
import pygame
from src.config import *

class TouchInterface:
    def __init__(self):
        # Начальные позиции (дефолтные)
        self.joy_x = 120
        self.joy_y = HEIGHT - 120
        self.joy_radius = 60
        self.stick_radius = 25
        
        # Стик (внутренняя часть джойстика)
        self.stick_x = self.joy_x
        self.stick_y = self.joy_y
        
        # Кнопка действия
        self.btn_x = WIDTH - 140
        self.btn_y = HEIGHT - 140
        self.btn_radius = 50
        
        # Хитбоксы для отслеживания кликов
        self.update_hitboxes()

        # Флаги состояний
        self.is_dragging_stick = False  # Тянем ли стик для ходьбы
        self.edit_mode = False          # Включен ли режим настройки кнопок
        self.dragging_joy_base = False  # Тянем ли сам джойстик в настройках
        self.dragging_btn_base = False  # Тянем ли саму кнопку в настройках

    def update_hitboxes(self):
        """Обновляет зоны клика при изменении координат"""
        self.joy_rect = pygame.Rect(self.joy_x - self.joy_radius, self.joy_y - self.joy_radius, self.joy_radius * 2, self.joy_radius * 2)
        self.btn_rect = pygame.Rect(self.btn_x - self.btn_radius, self.btn_y - self.btn_radius, self.btn_radius * 2, self.btn_radius * 2)

    def draw(self, screen):
        # Если включен режим настройки, рисуем полупрозрачный или мигающий фон/текст-подсказку
        if self.edit_mode:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))  # Затемнение экрана
            screen.blit(overlay, (0, 0))
            
            # Рамки вокруг настраиваемых элементов, чтобы было понятно, что их можно двигать
            pygame.draw.rect(screen, YELLOW, self.joy_rect.inflate(10, 10), 2, border_radius=10)
            pygame.draw.rect(screen, YELLOW, self.btn_rect.inflate(10, 10), 2, border_radius=10)

        # Рисуем подложку джойстика (в режиме настройки она подсвечивается желтым)
        joy_color = YELLOW if self.dragging_joy_base else GRAY
        pygame.draw.circle(screen, joy_color, (int(self.joy_x), int(self.joy_y)), self.joy_radius, 4)
        
        # Рисуем стик
        pygame.draw.circle(screen, DARK_GRAY, (int(self.stick_x), int(self.stick_y)), self.stick_radius)

        # Рисуем кнопку действия
        btn_base_color = YELLOW if self.dragging_btn_base else BLUE
        pygame.draw.circle(screen, btn_base_color, (int(self.btn_x), int(self.btn_y)), self.btn_radius)
        pygame.draw.circle(screen, WHITE, (int(self.btn_x), int(self.btn_y)), self.btn_radius, 3)

    def handle_event(self, event):
        dx, dy = 0, 0
        action_triggered = False
        mx, my = pygame.mouse.get_pos() if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION] else (0, 0)

        # --- РЕЖИМ НАСТРОЙКИ УПРАВЛЕНИЯ (КАСТОМИЗАЦИЯ) ---
        if self.edit_mode:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Проверяем, что именно хочет схватить и переместить игрок
                if ((mx - self.joy_x) ** 2 + (my - self.joy_y) ** 2) <= self.joy_radius ** 2:
                    self.dragging_joy_base = True
                elif self.btn_rect.collidepoint(mx, my):
                    self.dragging_btn_base = True

            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragging_joy_base = False
                self.dragging_btn_base = False
                self.stick_x = self.joy_x
                self.stick_y = self.joy_y
                self.update_hitboxes()

            elif event.type == pygame.MOUSEMOTION:
                # Ограничиваем, чтобы кнопки не улетали за границы экрана
                if self.dragging_joy_base:
                    self.joy_x = max(self.joy_radius, min(mx, WIDTH - self.joy_radius))
                    self.joy_y = max(self.joy_radius, min(my, HEIGHT - self.joy_radius))
                    self.stick_x, self.stick_y = self.joy_x, self.joy_y
                elif self.dragging_btn_base:
                    self.btn_x = max(self.btn_radius, min(mx, WIDTH - self.btn_radius))
                    self.btn_y = max(self.btn_radius, min(my, HEIGHT - self.btn_radius))
                    self.update_hitboxes()
            
            return dx, dy, action_triggered  # В режиме настройки персонаж ходить не должен

        # --- ОБЫЧНЫЙ ИГРОВОЙ РЕЖИМ ---
        if event.type == pygame.MOUSEBUTTONDOWN:
            sq_dist = (mx - self.joy_x) ** 2 + (my - self.joy_y) ** 2
            if sq_dist <= self.joy_radius ** 2:
                self.is_dragging_stick = True
            
            if self.btn_rect.collidepoint(mx, my):
                action_triggered = True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_dragging_stick = False
            self.stick_x = self.joy_x
            self.stick_y = self.joy_y

        elif event.type == pygame.MOUSEMOTION and self.is_dragging_stick:
            vx = mx - self.joy_x
            vy = my - self.joy_y
            dist = (vx ** 2 + vy ** 2) ** 0.5

            if dist <= self.joy_radius:
                self.stick_x = mx
                self.stick_y = my
            else:
                self.stick_x = self.joy_x + (vx / dist) * self.joy_radius
                self.stick_y = self.joy_y + (vy / dist) * self.joy_radius

            if abs(self.stick_x - self.joy_x) > 20:
                dx = 1 if self.stick_x > self.joy_x else -1
            if abs(self.stick_y - self.joy_y) > 20:
                dy = 1 if self.stick_y > self.joy_y else -1

        return dx, dy, action_triggered

def draw_button(screen, text, font, rect, base_color, text_color):
    pygame.draw.rect(screen, base_color, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
    
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    screen.blit(text_surf, text_rect)
