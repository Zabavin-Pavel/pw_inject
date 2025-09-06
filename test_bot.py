from pwbot import Bot
import time

bot = Bot()

while True:
    hp = bot.get_hp()
    mp = bot.get_mp()
    print(f"HP: {hp:.1f}, MP: {mp:.1f}")
    time.sleep(1)
