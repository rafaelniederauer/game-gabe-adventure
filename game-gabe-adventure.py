import argparse
from game import Game

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gabe Adventure Platformer')
    parser.add_argument('--level', type=int, default=1, help='Starting level number (default: 1)')
    args = parser.parse_args()

    game = Game(start_level=args.level)
    game.run()
