# wps
起動しているプロセスのコマンドライン一覧を見るコマンド(wmic processのラッパー)。

<!-- toc -->
- [wps](#wps)
  - [Overview](#overview)
  - [Demo](#demo)
    - [見る](#見る)
    - [殺す](#殺す)
  - [Requirement](#requirement)
  - [FAQ](#faq)
    - [Q: Kill と Terminate の違いは？](#q-kill-と-terminate-の違いは)
    - [Q: 出力フォーマットには何がありますか？](#q-出力フォーマットには何がありますか)
    - [Q: 出力される PID って桁揃えとか入ってます？](#q-出力される-pid-って桁揃えとか入ってます)
  - [License](#license)
  - [Author](#author)

## Overview
起動しているプロセスのコマンドラインを知りたい時があるのですが、

- タスクマネージャや Process Explorer など GUI → 少々扱いづらい
- `tasklist` コマンド → コマンドラインが出ないので論外
- `wmic process` コマンド → 引数が煩雑なのと、出力に余計な空行が入って見辛い

というわけで何か良い手段は無いかと考えて、「個人的に使う引数も限られてるし wmic process の簡単なラッパーでいいか」と思い、書いてみたところ、意外と使えそうだったので公開します。

## Demo

### 見る
引数無しで実行。

```
$ python wps.py
    0 
    4 
  292 \SystemRoot\System32\smss.exe
  580 wininit.exe
  640 C:\Windows\system32\services.exe
  828 "C:\Program Files\Mozilla Firefox\firefox.exe"
  836 C:\Windows\system32\svchost.exe -k DcomLaunch
...
```

出力フォーマット指定。 (PIDとキャプションとコマンドライン)

```
$ python wps.py -f "p c l"
    0 System Idle Process 
    4 System 
  292 smss.exe \SystemRoot\System32\smss.exe
  580 wininit.exe wininit.exe
  640 services.exe C:\Windows\system32\services.exe
  828 firefox.exe "C:\Program Files\Mozilla Firefox\firefox.exe"
  836 svchost.exe C:\Windows\system32\svchost.exe -k DcomLaunch
...
```

出力フォーマット指定その2。 (PIDと生成日時とキャプション)

```
$ python wps.py -f "p d c"
    0 2017/09/11 08:20:03 System Idle Process
    4 2017/09/11 08:20:03 System
  292 2017/09/11 08:20:03 smss.exe
  580 2017/09/11 08:21:27 wininit.exe
  640 2017/09/11 08:21:28 services.exe
  828 2017/09/12 08:25:57 firefox.exe
  836 2017/09/11 08:21:29 svchost.exe
...
```

生成時刻で降順ソート。 (--descが無い場合は昇順)

```
$ python wps.py -f "d c" --desc
2017/09/14 11:37:00 cmd.exe
2017/09/14 11:37:00 WmiPrvSE.exe
2017/09/14 11:37:00 WMIC.exe
2017/09/14 11:36:59 python.exe
2017/09/14 11:36:59 clip.exe
2017/09/14 11:26:37 Hidemaru.exe
2017/09/14 11:04:53 python.exe
...
```

### 殺す
PID を指定してプロセスを殺すことができる。以下は自分で立ち上げた notepad.exe を試しに殺してみた例。

```
$ notepad

$ python wps.py -f "p l" notepad
 7048 notepad.exe

$ python wps.py -k 7048
成功: PID 7048 のプロセスに強制終了のシグナルを送信しました。

$ python wps.py -f "p l" notepad

$ python wps.py -k 7048
エラー: プロセス "7048" が見つかりませんでした。
```

`-k` ではなく `-t` を使うと Terminate(強制終了) を実行する。

## Requirement
- Windows 7+
- Python 2.7

## FAQ

### Q: Kill と Terminate の違いは？
A: たとえば「編集されたメモ帳ウィンドウ」を殺す場合、Kill だと「保存しますか？」ダイアログが出るだけですが、Terminate だとダイアログも出ずに強制終了します。

### Q: 出力フォーマットには何がありますか？
A: 以下が使えます。

- p : PID
- l : command Line。コマンドライン
- d : creation Date。プロセス生成日時
- c : Caption。タイトル

たとえば PID、コマンドラインの順に表示したい場合は `python wps.py -f "p l"` のように指定します。

Usage にもしれっと書いてます。

```
$ python wps.py -h
usage: wps.py [-h] [-f FORMAT] [--desc] [-k KILL] [-t TERMINATE]
              [keyword [keyword ...]]

positional arguments:
  keyword               Keywords to extract lines with lowercase-AND partial
                        search. (default: )

optional arguments:
  -h, --help            show this help message and exit
  -f FORMAT, --format FORMAT
                        A combination of p=PID, d=creationDate, c=Caption and
                        l=commandLine (default: p l)
  --desc                Use DESC order. If not given, use ASC order. (default:
                        False)
  -k KILL, --kill KILL  A PID being killed. (default: None)
  -t TERMINATE, --terminate TERMINATE
                        A PID being killed forcely. (default: None)
```

### Q: 出力される PID って桁揃えとか入ってます？
A: 入ってます。5桁で揃えてます。コマンドラインオプションを単純にするため5桁揃え固定にしています。

## License
[MIT License](LICENSE)

## Author
[stakiran](https://github.com/stakiran)
