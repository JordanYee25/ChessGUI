# file: chess_gui_pygame_py_chess.py
"""
Pygame Chess GUI using python-chess as the rules engine.

Install:
  pip install pygame chess

Controls
- Left click: select / move
- Promotion: press Q/R/B/N
- R: restart
- ESC: quit
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pygame
import chess

Coord = Tuple[int, int]  # (row, col), row 0 = rank 8, col 0 = file a

FILES = "abcdefgh"
RANKS = "87654321"

UNICODE_PIECES = {
    "K": "♔",
    "Q": "♕",
    "R": "♖",
    "B": "♗",
    "N": "♘",
    "P": "♙",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}

PROMO_KEY_TO_PTYPE = {
    pygame.K_q: chess.QUEEN,
    pygame.K_r: chess.ROOK,
    pygame.K_b: chess.BISHOP,
    pygame.K_n: chess.KNIGHT,
}


def rc_to_square(rc: Coord) -> chess.Square:
    """UI (row 0=rank8) -> python-chess square."""
    r, c = rc
    file_ = c
    rank_ = 7 - r
    return chess.square(file_, rank_)


def square_to_rc(sq: chess.Square) -> Coord:
    """python-chess square -> UI (row 0=rank8)."""
    file_ = chess.square_file(sq)
    rank_ = chess.square_rank(sq)
    r = 7 - rank_
    c = file_
    return (r, c)


def rc_to_alg(rc: Coord) -> str:
    r, c = rc
    return f"{FILES[c]}{RANKS[r]}"


@dataclass(frozen=True)
class PlayerInfo:
    name: str
    color: chess.Color  # chess.WHITE / chess.BLACK


class MoveLogger:
    def __init__(self, white: PlayerInfo, black: PlayerInfo, out_dir: str = ".") -> None:
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(out_dir, f"chess_moves_{ts}.log")
        self.white = white
        self.black = black
        self._write_header()

    def _write_header(self) -> None:
        lines = [
            f"Date: {dt.datetime.now().isoformat(sep=' ', timespec='seconds')}",
            f"White: {self.white.name}",
            f"Black: {self.black.name}",
            "",
        ]
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def append(self, board: chess.Board, san: str, move: chess.Move) -> None:
        uci = move.uci()
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"{board.fullmove_number}{'...' if board.turn == chess.BLACK else '.'} {san}   [{uci}]\n")

    def append_result(self, result: str, reason: str) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(f"\nResult: {result} ({reason})\n")


@dataclass
class UIConfig:
    square: int = 80
    board_pad: int = 20
    panel_w: int = 280
    top_pad: int = 20
    bottom_pad: int = 20

    @property
    def board_px(self) -> int:
        return self.square * 8

    @property
    def width(self) -> int:
        return self.board_pad * 2 + self.board_px + self.panel_w

    @property
    def height(self) -> int:
        return self.top_pad + self.board_px + self.bottom_pad


class TextInput:
    def __init__(self, rect: pygame.Rect, label: str, initial: str = "") -> None:
        self.rect = rect
        self.label = label
        self.text = initial
        self.active = False

    def handle_event(self, e: pygame.event.Event) -> None:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.active = self.rect.collidepoint(e.pos)
        if e.type == pygame.KEYDOWN and self.active:
            if e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.active = False
            else:
                if len(e.unicode) == 1 and len(self.text) < 24 and e.unicode.isprintable():
                    self.text += e.unicode

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, small: pygame.font.Font) -> None:
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 0, border_radius=6)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=6)
        label_s = small.render(self.label, True, (0, 0, 0))
        screen.blit(label_s, (self.rect.x, self.rect.y - 18))
        txt = font.render(self.text or (" " if self.active else ""), True, (0, 0, 0))
        screen.blit(txt, (self.rect.x + 8, self.rect.y + 8))


@dataclass
class PendingPromotion:
    from_sq: chess.Square
    to_sq: chess.Square
    color: chess.Color


class ChessGUI:
    def __init__(self) -> None:
        pygame.init()
        self.cfg = UIConfig()
        self.screen = pygame.display.set_mode((self.cfg.width, self.cfg.height))
        pygame.display.set_caption("Pygame Chess (python-chess)")

        self.clock = pygame.time.Clock()
        self.font_piece = self._make_font(52, prefer=("Segoe UI Symbol", "DejaVu Sans", "Arial Unicode MS"))
        self.font_ui = self._make_font(22, prefer=("Segoe UI", "Arial", "DejaVu Sans"))
        self.font_small = self._make_font(16, prefer=("Segoe UI", "Arial", "DejaVu Sans"))

        self.board = chess.Board()

        base_x = self.cfg.board_pad + self.cfg.board_px + 20
        self.input_white = TextInput(pygame.Rect(base_x, 80, self.cfg.panel_w - 40, 44), "White player", "White")
        self.input_black = TextInput(pygame.Rect(base_x, 160, self.cfg.panel_w - 40, 44), "Black player", "Black")
        self.players_set = False
        self.white = PlayerInfo("White", chess.WHITE)
        self.black = PlayerInfo("Black", chess.BLACK)
        self.logger: Optional[MoveLogger] = None

        self.selected_rc: Optional[Coord] = None
        self.legal_to_rcs: List[Coord] = []
        self.pending_promotion: Optional[PendingPromotion] = None
        self.result_text: Optional[str] = None
        self.result_reason: Optional[str] = None

    def _make_font(self, size: int, prefer: Tuple[str, ...]) -> pygame.font.Font:
        for name in prefer:
            try:
                return pygame.font.SysFont(name, size)
            except Exception:
                continue
        return pygame.font.SysFont(None, size)

    def run(self) -> None:
        while True:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)

    # ---------------- events ----------------

    def _handle_events(self) -> None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if not self.players_set:
                self.input_white.handle_event(e)
                self.input_black.handle_event(e)
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._commit_players()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    if self._start_button_rect().collidepoint(e.pos):
                        self._commit_players()
                continue

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if e.key == pygame.K_r:
                    self._restart()
                if self.pending_promotion is not None:
                    self._handle_promotion_key(e)

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.pending_promotion is not None or self.result_text is not None:
                    continue
                self._handle_board_click(e.pos)

    def _commit_players(self) -> None:
        wname = (self.input_white.text or "White").strip()
        bname = (self.input_black.text or "Black").strip()
        self.white = PlayerInfo(wname, chess.WHITE)
        self.black = PlayerInfo(bname, chess.BLACK)
        self.players_set = True
        self.logger = MoveLogger(self.white, self.black)
        self._restart(reset_players=False)

    def _restart(self, reset_players: bool = False) -> None:
        self.board.reset()
        self.selected_rc = None
        self.legal_to_rcs = []
        self.pending_promotion = None
        self.result_text = None
        self.result_reason = None
        if self.players_set and self.logger and not reset_players:
            self.logger = MoveLogger(self.white, self.black)

    def _handle_promotion_key(self, e: pygame.event.Event) -> None:
        if e.key not in PROMO_KEY_TO_PTYPE or self.pending_promotion is None:
            return
        promo = PROMO_KEY_TO_PTYPE[e.key]
        pm = self.pending_promotion
        move = chess.Move(pm.from_sq, pm.to_sq, promotion=promo)
        self.pending_promotion = None
        self._try_push_move(move)

    def _handle_board_click(self, pos: Tuple[int, int]) -> None:
        rc = self._pos_to_rc(pos)
        if rc is None:
            return

        sq = rc_to_square(rc)

        if self.selected_rc is None:
            piece = self.board.piece_at(sq)
            if piece is not None and piece.color == self.board.turn:
                self.selected_rc = rc
                self.legal_to_rcs = self._legal_dests_for_square(sq)
            return

        if rc == self.selected_rc:
            self.selected_rc = None
            self.legal_to_rcs = []
            return

        # Re-select your own piece
        piece = self.board.piece_at(sq)
        if piece is not None and piece.color == self.board.turn:
            self.selected_rc = rc
            self.legal_to_rcs = self._legal_dests_for_square(sq)
            return

        # Attempt move
        if rc not in self.legal_to_rcs:
            return

        from_sq = rc_to_square(self.selected_rc)
        to_sq = sq

        moving_piece = self.board.piece_at(from_sq)
        if moving_piece and moving_piece.piece_type == chess.PAWN:
            to_rank = chess.square_rank(to_sq)
            if to_rank in (0, 7):
                self.pending_promotion = PendingPromotion(from_sq=from_sq, to_sq=to_sq, color=self.board.turn)
                return

        move = chess.Move(from_sq, to_sq)
        self._try_push_move(move)

        self.selected_rc = None
        self.legal_to_rcs = []

    def _legal_dests_for_square(self, from_sq: chess.Square) -> List[Coord]:
        out: List[Coord] = []
        for m in self.board.legal_moves:
            if m.from_square == from_sq:
                out.append(square_to_rc(m.to_square))
        return out

    def _try_push_move(self, move: chess.Move) -> None:
        if move not in self.board.legal_moves:
            return

        san = self.board.san(move)  # must compute before push
        self.board.push(move)

        if self.logger:
            self.logger.append(self.board, san, move)

        self._update_result_if_over()

    def _update_result_if_over(self) -> None:
        if self.board.is_checkmate():
            self.result_text = "1-0" if self.board.turn == chess.BLACK else "0-1"
            self.result_reason = "Checkmate"
        elif self.board.is_stalemate():
            self.result_text = "1/2-1/2"
            self.result_reason = "Stalemate"
        elif self.board.is_insufficient_material():
            self.result_text = "1/2-1/2"
            self.result_reason = "Insufficient material"
        elif self.board.can_claim_fifty_moves():
            self.result_text = "1/2-1/2"
            self.result_reason = "50-move rule (claimable)"
        elif self.board.can_claim_threefold_repetition():
            self.result_text = "1/2-1/2"
            self.result_reason = "Threefold repetition (claimable)"
        else:
            return

        if self.logger and self.result_text and self.result_reason:
            self.logger.append_result(self.result_text, self.result_reason)

    # ---------------- drawing ----------------

    def _draw(self) -> None:
        self.screen.fill((235, 235, 235))
        self._draw_board()
        self._draw_panel()

        if not self.players_set:
            self._draw_start_overlay()
        if self.pending_promotion is not None:
            self._draw_promotion_overlay()

    def _board_origin(self) -> Tuple[int, int]:
        return (self.cfg.board_pad, self.cfg.top_pad)

    def _draw_board(self) -> None:
        ox, oy = self._board_origin()
        sq = self.cfg.square

        for r in range(8):
            for c in range(8):
                rect = pygame.Rect(ox + c * sq, oy + r * sq, sq, sq)
                light = (r + c) % 2 == 0
                pygame.draw.rect(self.screen, (240, 217, 181) if light else (181, 136, 99), rect)

        if self.selected_rc is not None:
            r, c = self.selected_rc
            rect = pygame.Rect(ox + c * sq, oy + r * sq, sq, sq)
            pygame.draw.rect(self.screen, (255, 255, 0), rect, 4)

        for rc in self.legal_to_rcs:
            tr, tc = rc
            center = (ox + tc * sq + sq // 2, oy + tr * sq + sq // 2)
            pygame.draw.circle(self.screen, (0, 0, 0), center, 8)

        for square, piece in self.board.piece_map().items():
            r, c = square_to_rc(square)
            symbol = piece.symbol()  # 'p','N', etc (case encodes color)
            glyph = UNICODE_PIECES.get(symbol, "?")
            surf = self.font_piece.render(glyph, True, (0, 0, 0))
            rect = surf.get_rect(center=(ox + c * sq + sq // 2, oy + r * sq + sq // 2 + 2))
            self.screen.blit(surf, rect)

        for c in range(8):
            label = self.font_small.render(FILES[c], True, (0, 0, 0))
            self.screen.blit(label, (ox + c * sq + 4, oy + 8 * sq - 18))
        for r in range(8):
            label = self.font_small.render(RANKS[r], True, (0, 0, 0))
            self.screen.blit(label, (ox + 4, oy + r * sq + 4))

    def _draw_panel(self) -> None:
        ox, oy = self._board_origin()
        panel_x = ox + self.cfg.board_px + 10
        panel_rect = pygame.Rect(panel_x, oy, self.cfg.panel_w - 20, self.cfg.board_px)
        pygame.draw.rect(self.screen, (255, 255, 255), panel_rect, 0, border_radius=10)
        pygame.draw.rect(self.screen, (0, 0, 0), panel_rect, 2, border_radius=10)

        x = panel_rect.x + 14
        y = panel_rect.y + 14

        def line(text: str, dy: int = 26) -> None:
            nonlocal y
            surf = self.font_ui.render(text, True, (0, 0, 0))
            self.screen.blit(surf, (x, y))
            y += dy

        if not self.players_set:
            line("Enter names → Start", 30)
            return

        line(f"White: {self.white.name}", 28)
        line(f"Black: {self.black.name}", 28)
        y += 10

        turn_name = self.white.name if self.board.turn == chess.WHITE else self.black.name
        line(f"Turn: {turn_name}", 28)
        line("Status: Check" if self.board.is_check() and self.result_text is None else "Status: OK", 28)
        line(f"Move: {self.board.fullmove_number}", 28)

        y += 10
        line("R: restart", 26)
        line("ESC: quit", 26)

        if self.logger:
            y += 10
            line("Log file:", 24)
            surf = self.font_small.render(os.path.basename(self.logger.path), True, (0, 0, 0))
            self.screen.blit(surf, (x, y))
            y += 24

        if self.result_text is not None:
            y += 18
            line(f"Result: {self.result_text}", 28)
            line(f"({self.result_reason})", 28)

    def _draw_start_overlay(self) -> None:
        overlay = pygame.Surface((self.cfg.width, self.cfg.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        base_x = self.cfg.board_pad + self.cfg.board_px + 20
        box = pygame.Rect(base_x - 10, 40, self.cfg.panel_w - 20, 250)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 0, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), box, 2, border_radius=12)

        title = self.font_ui.render("New Game", True, (0, 0, 0))
        self.screen.blit(title, (box.x + 14, box.y + 10))

        self.input_white.draw(self.screen, self.font_ui, self.font_small)
        self.input_black.draw(self.screen, self.font_ui, self.font_small)

        btn = self._start_button_rect()
        pygame.draw.rect(self.screen, (0, 0, 0), btn, 0, border_radius=10)
        txt = self.font_ui.render("Start", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=btn.center))

        hint = self.font_small.render("Press Enter or click Start", True, (0, 0, 0))
        self.screen.blit(hint, (box.x + 14, box.y + 220))

    def _start_button_rect(self) -> pygame.Rect:
        base_x = self.cfg.board_pad + self.cfg.board_px + 20
        return pygame.Rect(base_x, 220, self.cfg.panel_w - 40, 46)

    def _draw_promotion_overlay(self) -> None:
        overlay = pygame.Surface((self.cfg.width, self.cfg.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        box = pygame.Rect(self.cfg.board_pad + 60, self.cfg.top_pad + 200, self.cfg.board_px - 120, 160)
        pygame.draw.rect(self.screen, (255, 255, 255), box, 0, border_radius=12)
        pygame.draw.rect(self.screen, (0, 0, 0), box, 2, border_radius=12)

        title = self.font_ui.render("Promotion", True, (0, 0, 0))
        self.screen.blit(title, (box.x + 18, box.y + 16))

        msg = self.font_ui.render("Press Q / R / B / N", True, (0, 0, 0))
        self.screen.blit(msg, (box.x + 18, box.y + 54))

        # show symbols (based on mover color; mover is opposite of board.turn right now? no: pending move not pushed)
        mover = self.pending_promotion.color if self.pending_promotion else chess.WHITE
        y = box.y + 102
        x = box.x + 24
        for sym in ("q", "r", "b", "n"):
            s = sym.upper() if mover == chess.WHITE else sym
            glyph = UNICODE_PIECES[s]
            surf = self.font_piece.render(glyph, True, (0, 0, 0))
            self.screen.blit(surf, (x, y))
            x += 70

    # ---------------- coords ----------------

    def _pos_to_rc(self, pos: Tuple[int, int]) -> Optional[Coord]:
        ox, oy = self._board_origin()
        x, y = pos
        if not (ox <= x < ox + self.cfg.board_px and oy <= y < oy + self.cfg.board_px):
            return None
        c = (x - ox) // self.cfg.square
        r = (y - oy) // self.cfg.square
        return (int(r), int(c))


def main() -> None:
    ChessGUI().run()


if __name__ == "__main__":
    main()
