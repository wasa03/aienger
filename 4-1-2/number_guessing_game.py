import random

def number_guessing_game():
    """
    1～100の間の数字を当てるゲーム
    """
    # ①コンピューターが1～100の間の数字をランダムに選ぶ
    target_number = random.randint(1, 100)
    attempts = 0
    
    print("🎮 数当てゲームへようこそ！")
    print("1から100の間の数字を当ててください。\n")
    
    while True:
        try:
            # ②ユーザーがその数字を当てる
            guess = int(input("数字を入力してください: "))
            attempts += 1
            
            # 入力値の範囲チェック
            if guess < 1 or guess > 100:
                print("⚠️  1から100の間の数字を入力してください。\n")
                continue
            
            # ④正解時には「🎉 正解です！」と共に試行回数を表示する
            if guess == target_number:
                print(f"🎉 正解です！")
                print(f"試行回数: {attempts}回")
                break
            # ③ユーザーの入力に応じて、「もっと大きい」「もっと小さい」というヒントを出す
            # 誤差が5以下の場合は「少し」、それ以外は「もっと」と表示
            difference = abs(guess - target_number)
            if guess < target_number:
                if difference <= 5:
                    print("💡 少し大きい数字です。\n")
                else:
                    print("💡 もっと大きい数字です。\n")
            else:
                if difference <= 5:
                    print("💡 少し小さい数字です。\n")
                else:
                    print("💡 もっと小さい数字です。\n")
                
        except ValueError:
            print("⚠️  数字を入力してください。\n")
            continue

if __name__ == "__main__":
    number_guessing_game()
