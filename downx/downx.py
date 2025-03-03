import pyxel
import math
import random

def rects_collide(ax, ay, aw, ah, bx, by, bw, bh):
    """2つの矩形が衝突しているかどうかを判定する補助関数"""
    return not (ax + aw <= bx or ax >= bx + bw or ay + ah <= by or ay >= by + bh)

class App:
    def __init__(self):
        pyxel.init(160, 120, title="Vertical Scroller")
        
        # --- サウンド設定 ---
        # 背景BGM（音ID0）
        pyxel.sound(0).set("c2e2g2c3", "s", "6", "n", 30)
        pyxel.playm(0, loop=True)
        # プレイヤー噴射音（音ID1）：シュー風（低音ノイズ＋フェード）
        pyxel.sound(1).set("c1", "n", "3", "f", 10)
        # 敵弾発射時の音（音ID2）：短い金属音風（三角波 "t"）
        pyxel.sound(2).set("c2", "t", "2", "n", 5)
        # プレイヤー被弾時の音（音ID3）：どカーン音
        pyxel.sound(3).set("c4", "s", "3", "n", 20)
        # 衝突（ライフ減少）時の悲壮感漂う曲（音ID5）
        pyxel.sound(5).set("c0", "s", "4", "n", 50)
        self.thrust_playing = False

        # --- カウントダウン ---
        self.countdown_timer = 180  # 3秒

        # --- プレイヤー初期設定 ---
        self.player_x = 76
        self.player_y = 40    # 画面上部寄り
        self.player_w = 8
        self.player_h = 8
        self.player_speed = 2
        self.player_vy = 0
        self.gravity = 0.15   # 自由落下をより緩やかに
        self.thrust = -0.3
        self.max_up_velocity = -4
        self.max_down_velocity = 4

        # プレイヤーライフ（開始時3つ）
        self.lives = 3
        self.game_over = False

        # --- スクロール設定 ---
        self.scroll_y = 0
        self.scroll_speed = 0.5

        # --- 岩（障害物）の管理 ---
        self.rock_list = []
        self.next_rock_y = 50

        # --- 壁穴（横穴）の管理 ---
        self.wallholes = []
        # 壁穴生成間隔を10倍に増やす（20～30ピクセルごと）
        self.next_wallhole_y = 20

        # --- 敵パラメータ ---
        self.enemy_width = 8
        self.enemy_height = 8
        self.enemy_bullets = []

        pyxel.run(self.update, self.draw)

    def get_boundaries(self, world_y):
        """
        指定したワールド座標 world_y における左右の壁（通路）の境界を計算する。
        基本幅は100＋変動とします。
        """
        corridor_width = 100 + 20 * math.sin(world_y / 30.0)
        center = pyxel.width // 2
        left_base = center - int(corridor_width) // 2
        right_base = left_base + int(corridor_width)
        jitter = int(5 * math.sin(world_y / 10.0))
        return left_base + jitter, right_base + jitter

    def handle_collision_event(self):
        """敵または敵弾との衝突、または画面下端突き抜け時の処理：ライフを1減らし、悲壮な音を再生し、カウントダウンから再スタート"""
        pyxel.play(1, 5)  # 悲壮感漂う長い音（音ID5、チャンネル1）再生
        self.lives -= 1
        if self.lives > 0:
            # ライフが残っているなら、プレイヤーの位置と速度をリセットし、カウントダウン再設定
            self.player_x = 76
            self.player_y = 40
            self.player_vy = 0
            self.countdown_timer = 180  # 3秒カウントダウン
        else:
            self.game_over = True

    def update(self):
        # カウントダウン中は更新処理を行わない
        if self.countdown_timer > 0:
            self.countdown_timer -= 1
            return

        # ゲームオーバー時はリプレイ待ち（スペースキー）
        if self.game_over:
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.reset_game()
            return

        # --- プレイヤー噴射音 ---
        if pyxel.btn(pyxel.KEY_SPACE):
            if not self.thrust_playing:
                pyxel.play(3, 1, loop=True)
                self.thrust_playing = True
        else:
            if self.thrust_playing:
                pyxel.stop(3)
                self.thrust_playing = False

        # --- スクロール ---
        self.scroll_y += self.scroll_speed

        # --- 岩生成（必ず敵を乗せる） ---
        if self.scroll_y + pyxel.height > self.next_rock_y:
            rock_width = random.randint(20, 50)
            rock_height = random.randint(5, 15)
            left_bound, right_bound = self.get_boundaries(self.next_rock_y)
            rock = {"y": self.next_rock_y, "width": rock_width, "height": rock_height}
            # 岩は左右の壁にくっつく
            side = random.choice([0, 1])
            if side == 0:
                rock["x"] = left_bound
            else:
                rock["x"] = right_bound - rock_width
            # 敵生成：必ず岩に乗せる
            enemy = {}
            enemy["x"] = rock["x"] + (rock_width - self.enemy_width) // 2
            enemy["y"] = self.next_rock_y - self.enemy_height
            enemy["can_shoot"] = True
            if self.scroll_y < 1000:
                enemy["type"] = "normal"
            elif self.scroll_y < 2000:
                enemy["type"] = random.choices(["normal", "rapid"], weights=[70,30])[0]
            else:
                enemy["type"] = random.choices(["normal", "rapid", "burst"], weights=[50,30,20])[0]
            if enemy["type"] == "normal":
                enemy["shoot_cooldown"] = random.randint(60, 150)
            elif enemy["type"] == "rapid":
                enemy["shoot_cooldown"] = random.randint(30, 80)
            elif enemy["type"] == "burst":
                enemy["shoot_cooldown"] = random.randint(120, 180)
            enemy["phase"] = random.uniform(0, 2 * math.pi)
            rock["enemy"] = enemy
            self.rock_list.append(rock)
            self.next_rock_y += random.randint(50, 100)

        # --- 壁穴生成（横穴）---
        if self.scroll_y + pyxel.height > self.next_wallhole_y:
            hole_width = 10
            hole_height = 4
            side = random.choice([0, 1])
            wh = {"y": self.next_wallhole_y, "width": hole_width, "height": hole_height, "side": side}
            left_bound, right_bound = self.get_boundaries(self.next_wallhole_y)
            if side == 0:
                wh["x"] = left_bound
            else:
                wh["x"] = right_bound - hole_width
            self.wallholes.append(wh)
            self.next_wallhole_y += random.randint(20, 30)
        self.wallholes = [wh for wh in self.wallholes if wh["y"] - self.scroll_y < pyxel.height + 10]

        # --- 敵更新 ---
        for rock in self.rock_list:
            if "enemy" in rock:
                enemy = rock["enemy"]
                enemy["y"] = rock["y"] - self.enemy_height
                if self.scroll_y >= 3000:
                    enemy["x"] = rock["x"] + (rock["width"] - self.enemy_width) // 2 \
                        + int(5 * math.sin(pyxel.frame_count / 30 + enemy["phase"]))
                else:
                    enemy["x"] = rock["x"] + (rock["width"] - self.enemy_width) // 2
                if enemy.get("can_shoot"):
                    enemy["shoot_cooldown"] -= 1
                    if enemy["shoot_cooldown"] <= 0:
                        enemy_cx = enemy["x"] + self.enemy_width / 2
                        enemy_cy = enemy["y"] + self.enemy_height / 2
                        player_cx = self.player_x + self.player_w / 2
                        player_cy = self.player_y + self.player_h / 2
                        dx = player_cx - enemy_cx
                        dy = player_cy - enemy_cy
                        bullet_speed = 2.5
                        if enemy["type"] in ["normal", "rapid"]:
                            if dy > 0:
                                dy = 0
                                vx = bullet_speed * (1 if dx >= 0 else -1)
                                vy = 0
                            else:
                                dist = math.hypot(dx, dy)
                                if dist == 0:
                                    dist = 1
                                vx = bullet_speed * dx / dist
                                vy = bullet_speed * dy / dist
                            bullet = {
                                "x": enemy_cx - 1,
                                "y": enemy_cy,
                                "width": 2,
                                "height": 4,
                                "vx": vx,
                                "vy": vy
                            }
                            self.enemy_bullets.append(bullet)
                            pyxel.play(2, 2)  # バン音再生（音ID2）
                            if enemy["type"] == "normal":
                                min_cd = max(10, 60 - int(self.scroll_y / 200))
                                max_cd = max(30, 150 - int(self.scroll_y / 200))
                            else:  # rapid
                                min_cd = max(5, 30 - int(self.scroll_y / 300))
                                max_cd = max(15, 80 - int(self.scroll_y / 300))
                            enemy["shoot_cooldown"] = random.randint(min_cd, max_cd)
                        elif enemy["type"] == "burst":
                            if dy > 0:
                                base_angle = 0
                            else:
                                base_angle = math.atan2(dy, dx)
                            for offset in [-0.26, 0, 0.26]:
                                angle = base_angle + offset
                                vx = bullet_speed * math.cos(angle)
                                vy = bullet_speed * math.sin(angle)
                                bullet = {
                                    "x": enemy_cx - 1,
                                    "y": enemy_cy,
                                    "width": 2,
                                    "height": 4,
                                    "vx": vx,
                                    "vy": vy
                                }
                                self.enemy_bullets.append(bullet)
                            pyxel.play(2, 2)
                            min_cd = max(80, 120 - int(self.scroll_y / 200))
                            max_cd = max(120, 180 - int(self.scroll_y / 200))
                            enemy["shoot_cooldown"] = random.randint(min_cd, max_cd)

        # --- 敵弾更新 ---
        for bullet in self.enemy_bullets:
            bullet["x"] += bullet["vx"]
            bullet["y"] += bullet["vy"]
        new_enemy_bullets = []
        for bullet in self.enemy_bullets:
            lb, rb = self.get_boundaries(bullet["y"])
            if bullet["x"] < lb or (bullet["x"] + bullet["width"]) > rb:
                continue
            new_enemy_bullets.append(bullet)
        self.enemy_bullets = [
            b for b in new_enemy_bullets
            if (-10 < b["x"] < pyxel.width + 10 and (b["y"] - self.scroll_y) < pyxel.height + 10 and b["y"] > self.scroll_y - 10)
        ]

        # --- プレイヤー水平移動 ---
        old_x = self.player_x
        new_x = self.player_x
        if pyxel.btn(pyxel.KEY_LEFT):
            new_x -= self.player_speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            new_x += self.player_speed
        player_center_y = self.player_y + self.player_h // 2
        left_bound, right_bound = self.get_boundaries(player_center_y)
        if new_x < left_bound:
            new_x = left_bound
        if new_x + self.player_w > right_bound:
            new_x = right_bound - self.player_w
        for rock in self.rock_list:
            if rects_collide(new_x, self.player_y, self.player_w, self.player_h,
                             rock["x"], rock["y"], rock["width"], rock["height"]):
                new_x = old_x
                break
        self.player_x = new_x

        # --- プレイヤー垂直移動 ---
        old_y = self.player_y
        if pyxel.btn(pyxel.KEY_SPACE):
            self.player_vy += self.thrust
        else:
            self.player_vy += self.gravity
        if self.player_vy < self.max_up_velocity:
            self.player_vy = self.max_up_velocity
        if self.player_vy > self.max_down_velocity:
            self.player_vy = self.max_down_velocity
        new_y = self.player_y + self.player_vy
        if self.player_vy < 0 and new_y < self.scroll_y:
            new_y = self.scroll_y
            self.player_vy = 0
        self.player_y = new_y

        # --- プラットフォーム（岩＆壁穴）衝突判定 ---
        platforms = []
        for rock in self.rock_list:
            platforms.append({
                "x": rock["x"],
                "y": rock["y"],
                "width": rock["width"],
                "height": rock["height"]
            })
        for wh in self.wallholes:
            platforms.append({
                "x": wh["x"],
                "y": wh["y"],
                "width": wh["width"],
                "height": wh["height"]
            })
        for plat in platforms:
            if self.player_x + self.player_w > plat["x"] and self.player_x < plat["x"] + plat["width"]:
                plat_top = plat["y"]
                plat_bottom = plat["y"] + plat["height"]
                if self.player_vy > 0 and old_y + self.player_h <= plat_top + 2 and self.player_y + self.player_h >= plat_top:
                    self.player_y = plat_top - self.player_h
                    self.player_vy = 0
                elif self.player_vy < 0 and old_y >= plat_bottom - 2 and self.player_y <= plat_bottom:
                    self.player_y = plat_bottom
                    self.player_vy = 0

        # --- プレイヤーと敵の衝突判定 ---
        for rock in self.rock_list:
            if "enemy" in rock:
                enemy = rock["enemy"]
                if rects_collide(self.player_x, self.player_y, self.player_w, self.player_h,
                                 enemy["x"], enemy["y"], self.enemy_width, self.enemy_height):
                    self.handle_collision_event()
                    break

        # --- プレイヤーと敵弾の衝突判定 ---
        for bullet in self.enemy_bullets:
            if rects_collide(bullet["x"], bullet["y"], bullet["width"], bullet["height"],
                             self.player_x, self.player_y, self.player_w, self.player_h):
                self.handle_collision_event()
                break

        # --- 画面下端突き抜け判定 ---
        if self.player_y - self.scroll_y > pyxel.height:
            self.handle_collision_event()

        # --- 画面外の岩・壁穴削除 ---
        self.rock_list = [rock for rock in self.rock_list if rock["y"] - self.scroll_y < pyxel.height + 10]
        self.wallholes = [wh for wh in self.wallholes if wh["y"] - self.scroll_y < pyxel.height + 10]

        # --- ゲームオーバー判定 ---
        # ゲームオーバーは handle_collision_event() 内でライフ0になったときに設定

    def reset_game(self):
        self.player_x = 76
        self.player_y = 40
        self.player_vy = 0
        self.scroll_y = 0
        self.rock_list = []
        self.wallholes = []
        self.next_rock_y = 50
        self.next_wallhole_y = 20
        self.enemy_bullets = []
        self.countdown_timer = 180
        self.lives = 3
        self.game_over = False
        self.thrust_playing = False
        pyxel.stop(3)

    def draw(self):
        pyxel.cls(0)
        # --- 背景（壁：茶色＝色4） ---
        for screen_y in range(pyxel.height):
            world_y = screen_y + self.scroll_y
            left_bound, right_bound = self.get_boundaries(world_y)
            pyxel.line(0, screen_y, left_bound, screen_y, 4)
            pyxel.line(right_bound, screen_y, pyxel.width, screen_y, 4)
        # --- 岩と敵 ---
        for rock in self.rock_list:
            screen_rock_y = rock["y"] - self.scroll_y
            if -rock["height"] < screen_rock_y < pyxel.height:
                pyxel.rect(rock["x"], screen_rock_y, rock["width"], rock["height"], 4)
            if "enemy" in rock:
                enemy = rock["enemy"]
                screen_enemy_y = enemy["y"] - self.scroll_y
                if enemy["type"] == "normal":
                    enemy_color = 9
                elif enemy["type"] == "rapid":
                    enemy_color = 10
                elif enemy["type"] == "burst":
                    enemy_color = 13
                pyxel.rect(enemy["x"], screen_enemy_y, self.enemy_width, self.enemy_height, enemy_color)
        # --- 壁穴描画（壁と同じ茶色＝色4） ---
        for wh in self.wallholes:
            screen_wh_y = wh["y"] - self.scroll_y
            pyxel.rect(wh["x"], screen_wh_y, wh["width"], wh["height"], 4)
        # --- 敵弾 ---
        for bullet in self.enemy_bullets:
            screen_bullet_y = bullet["y"] - self.scroll_y
            pyxel.rect(bullet["x"], screen_bullet_y, bullet["width"], bullet["height"], 9)
        # --- プレイヤー ---
        screen_player_y = self.player_y - self.scroll_y
        pyxel.rect(self.player_x, screen_player_y, self.player_w, self.player_h, 11)
        # --- スコアとライフ表示 ---
        pyxel.text(5, 5, "SCORE: " + str(int(self.scroll_y)), 7)
        pyxel.text(5, 15, "LIVES: " + str(self.lives), 7)
        # --- カウントダウン表示 ---
        if self.countdown_timer > 0:
            count = math.ceil(self.countdown_timer / 60)
            text = str(count)
            text_width = len(text) * 8
            pyxel.text((pyxel.width - text_width) // 2, pyxel.height // 2, text, 7)
        # --- ゲームオーバー表示 ---
        if self.game_over:
            game_over_text = "GAME OVER"
            text_width = len(game_over_text) * 8
            pyxel.text((pyxel.width - text_width) // 2, pyxel.height // 2, game_over_text, 8)
            pyxel.text((pyxel.width - text_width) // 2, pyxel.height // 2 + 10, "Press SPACE to replay", 7)

App()

