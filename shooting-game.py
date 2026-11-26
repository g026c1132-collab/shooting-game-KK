"""ASCIIインベーダー風シューティング（標準ライブラリのみ）。

A/D・←/→で移動、Spaceで射撃、P一時停止、Rリスタート、Q終了。
上から降ってくる敵を撃って得点を稼ぎます。敵が最下段まで降りたり、
自機に衝突するとライフが減ります。ライフが0で終了。

【オブジェクト指向の発展教材 ★★★～★★★★★】
重要なクラス：Player（自機）、Bullet（弾）、Enemy（敵）、ShootingGame（管理）。
Enemyを継承して敵の種類を作れます。既存のHeavyEnemy/FastEnemyを参照。
   class ZigzagEnemy(Enemy):
       symbol = 'Z'
       points = 30
       def update(self):
           super().update()
           # ここに左右へ移動する処理を足す
改造の入口：敵のHP・降下速度・出現頻度・弾速・得点を調整。
発展：横移動する敵、敵弾、広範囲の弾、2x2のボス、複数段の編隊など。
画面とキー入力は terminal_io.py に分離してあります。
"""
from __future__ import annotations
from dataclasses import dataclass
import random
import time
from terminal_io import Terminal, paint

WIDTH, HEIGHT = 32, 18
FRAME = 0.07


@dataclass
class Player:
    x: int = WIDTH // 2
    y: int = HEIGHT - 1
    lives: int = 3
    symbol: str = '^'

    def move(self, direction):
        self.x = max(0, min(WIDTH - 1, self.x + direction))


@dataclass
class Bullet:
    x: int
    y: int
    dy: int = -1
    symbol: str = '*'

    def update(self):
        self.y += self.dy


class Enemy:
    symbol = 'A'
    hp = 1
    points = 10
    speed = 9  # この回数の更新ごとに1マス降下（小さいほど速い）

    def __init__(self, x, y=0):
        self.x, self.y = x, y
        self.hp = type(self).hp
        self.age = 0

    def update(self):
        self.age += 1
        if self.age % self.speed == 0:
            self.y += 1

    def take_hit(self):
        self.hp -= 1
        return self.hp <= 0


class HeavyEnemy(Enemy):
    symbol = 'H'
    hp = 3
    points = 30
    speed = 12


class FastEnemy(Enemy):
    symbol = 'F'
    hp = 1
    points = 20
    speed = 5


class ShootingGame:
    def __init__(self, rng=None):
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.score = 0
        self.tick = 0
        self.cooldown = 0
        self.paused = False
        self.game_over = False

    def fire(self):
        if self.game_over or self.paused or self.cooldown:
            return False
        self.bullets.append(Bullet(self.player.x, self.player.y - 1))
        self.cooldown = 3
        return True

    def spawn_enemy(self):
        enemy_type = self.rng.choices([Enemy, FastEnemy, HeavyEnemy], weights=[7, 2, 1])[0]
        self.enemies.append(enemy_type(self.rng.randrange(WIDTH)))

    def update(self):
        if self.game_over or self.paused:
            return
        self.tick += 1
        if self.cooldown:
            self.cooldown -= 1
        interval = max(7, 22 - self.score // 150)
        if self.tick % interval == 0:
            self.spawn_enemy()
        for bullet in self.bullets:
            bullet.update()
        for enemy in self.enemies:
            enemy.update()
        # 命中弾は1発につき敵1体に当たる。残HPが0なら撃墜。
        for bullet in list(self.bullets):
            if bullet.y < 0:
                self.bullets.remove(bullet)
                continue
            for enemy in list(self.enemies):
                if bullet.x == enemy.x and bullet.y == enemy.y:
                    if enemy.take_hit():
                        self.enemies.remove(enemy)
                        self.score += enemy.points
                    self.bullets.remove(bullet)
                    break
        # 最下段に達した敵は自機を傷つける。ライフが尽きたら終了。
        for enemy in list(self.enemies):
            if enemy.y >= self.player.y:
                self.enemies.remove(enemy)
                self.player.lives -= 1
        if self.player.lives <= 0:
            self.game_over = True

    def render(self):
        board = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]
        for enemy in self.enemies:
            if 0 <= enemy.y < HEIGHT:
                board[enemy.y][enemy.x] = enemy.symbol
        for bullet in self.bullets:
            if 0 <= bullet.y < HEIGHT:
                board[bullet.y][bullet.x] = bullet.symbol
        board[self.player.y][self.player.x] = self.player.symbol
        out = ['=== ASCII SHOOTING ===', f'SCORE {self.score}  LIFE {self.player.lives}  ENEMY {len(self.enemies)}', '+' + '-' * WIDTH + '+']
        out += ['|' + ''.join(row) + '|' for row in board]
        out += ['+' + '-' * WIDTH + '+', 'A/D:移動 Space:射撃 P:停止 R:再開 Q:終了', 'A:通常 H:重装甲(3発) F:高速']
        if self.paused:
            out.append('--- PAUSED ---')
        if self.game_over:
            out.append('--- GAME OVER --- Rで再挑戦 / Qで終了')
        return out


def main():
    game = ShootingGame()
    print('ASCII SHOOTING: Enterで開始 / Qで終了')
    if input().strip().lower() == 'q':
        return
    with Terminal() as terminal:
        last = time.monotonic()
        while True:
            paint(game.render())
            key = terminal.read_key()
            if key == 'q':
                break
            if key == 'r':
                game.reset()
                last = time.monotonic()
            elif key == 'p':
                game.paused = not game.paused
                last = time.monotonic()
            elif not game.game_over and not game.paused:
                if key in ('a', 'left'):
                    game.player.move(-1)
                elif key in ('d', 'right'):
                    game.player.move(1)
                elif key == ' ':
                    game.fire()
            now = time.monotonic()
            if now - last >= FRAME:
                game.update()
                last = now
            time.sleep(0.025)
    print('シューティングを終了しました。')


if __name__ == '__main__':
    main()