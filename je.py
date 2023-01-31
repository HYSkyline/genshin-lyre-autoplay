# -*- coding:utf-8 -*-

import ctypes
import sys
import time

# C 语言中兼容的 SendInput 键鼠统一输入函数。
SendInput = ctypes.windll.user32.SendInput
# C 语言指针对象
PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
	"""键盘输入类"""
	_fields_ = [
		("wVk", ctypes.c_ushort),
		("wScan", ctypes.c_ushort),
		("dwFlags", ctypes.c_ulong),
		("time", ctypes.c_ulong),
		("dwExtraInfo", PUL)
	]


class HardwareInput(ctypes.Structure):
	"""硬件输入类"""
	_fields_ = [
		("uMsg", ctypes.c_ulong),
		("wParamL", ctypes.c_short),
		("wParamH", ctypes.c_ushort)
	]


class MouseInput(ctypes.Structure):
	"""鼠标输入类"""
	_fields_ = [
		("dx", ctypes.c_long),
		("dy", ctypes.c_long),
		("mouseData", ctypes.c_ulong),
		("dwFlags", ctypes.c_ulong),
		("time", ctypes.c_ulong),
		("dwExtraInfo", PUL)
	]


class InputI(ctypes.Union):
	"""输入联合体类"""
	_fields_ = [
		("ki", KeyBdInput),
		("mi", MouseInput),
		("hi", HardwareInput)
	]


class Input(ctypes.Structure):
	"""输入类"""
	_fields_ = [
		("type", ctypes.c_ulong),
		("ii", InputI)
	]


def press_key(hex_keycode):
	extra = ctypes.c_ulong(0)
	ii_ = InputI()
	ii_.ki = KeyBdInput(0, hex_keycode, 0x0008, 0, ctypes.pointer(extra))
	cmd = Input(ctypes.c_ulong(1), ii_)
	ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))


def release_key(hex_keycode):
	extra = ctypes.c_ulong(0)
	ii_ = InputI()
	ii_.ki = KeyBdInput(0, hex_keycode, 0x0008 | 0x0002, 0, ctypes.pointer(extra))
	cmd = Input(ctypes.c_ulong(1), ii_)
	ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))


def mouse_move(lng, lat):
	extra = ctypes.c_ulong(0)
	ii_ = InputI()
	ii_.mi = MouseInput(lng, lat, 0, 0x0001 | 0x8000, 1, ctypes.pointer(extra))
	cmd = Input(ctypes.c_ulong(0), ii_)
	ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))


def left_click(lng, lat):
	extra = ctypes.c_ulong(0)
	ii_ = InputI()
	ii_.mi = MouseInput(lng, lat, 0, 0x0002, 0, ctypes.pointer(extra))
	cmd = Input(ctypes.c_ulong(0), ii_)
	ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))


def left_release(lng, lat):
	extra = ctypes.c_ulong(0)
	ii_ = InputI()
	ii_.mi = MouseInput(lng, lat, 0, 0x0004, 0, ctypes.pointer(extra))
	cmd = Input(ctypes.c_ulong(0), ii_)
	ctypes.windll.user32.SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))


def is_admin():
	try:
		# 检测是否为管理员身份运行
		return ctypes.windll.shell32.IsUserAnAdmin()
	except RuntimeError:
		return False


def main(fname, rhythm):
	key_map = {
		"q": 0x10, "w": 0x11, "e": 0x12, "r": 0x13, "t": 0x14, "y": 0x15, "u": 0x16,
		"a": 0x1e, "s": 0x1f, "d": 0x20, "f": 0x21, "g": 0x22, "h": 0x23, "j": 0x24,
		"z": 0x2c, "x": 0x2d, "c": 0x2e, "v": 0x2f, "b": 0x30, "n": 0x31, "m": 0x32,
		" ": 0x39
	}
	score_map = {
		'+1': 'q', '+2': 'w', '+3': 'e', '+4': 'r', '+5': 't', '+6': 'y', '+7': 'u',
		'1': 'a', '2': 's', '3': 'd', '4': 'f', '5': 'g', '6': 'h', '7': 'j',
		'-1': 'z', '-2': 'x', '-3': 'c', '-4': 'v', '-5': 'b', '-6': 'n', '-7': 'm',
	}

	beat_list = score_read(fname, rhythm, score_map)
	print('beat parsed: ' + str(len(beat_list)))
	beat_play(beat_list, key_map)

	# print(beat_parse('-1(5+2)+2(5+5+2)', score_map))


def score_read(file_name, rhythm_time, score_map):
	f_score = open(file_name, 'r', encoding='utf-8')
	f_content = f_score.read()
	# rhythm_list结构: ['(ZGW) (BGW) ', '(SGW) (BQE) ', '(DQE) (BQT) ', '(SQT) (BQ) ', '(VQ) (ZQ) ']
	# rhythm_list结构: ['(-15+2) (-55+2) ', '(25+2) (-5+1+3) ', '(3+1+3) (-5+1+5) ', '(2+1+5) (-5+1) ']
	if f_content.find('/') > 0:
		rhythm_list = f_content.replace('\n', '').replace('（', '(').replace('）', ')').replace('[', '(').replace(']', ')').split('/')
	else:
		rhythm_list = f_content.replace('\n', '').replace('（', '(').replace('）', ')').replace('[', '(').replace(']', ')').split('\t')
	f_score.close()
	print('score read.')
	# beat_list结构: [[0.25, ['z', 'g', 'w']], [0.25, ['b', 'g', 'w']]]
	beat_list = []
	for i in range(len(rhythm_list)):
		# each: '(ZGW) (BGW)'
		# each: '(-15+2) (-55+2) '
		beat = beat_parse(rhythm_list[i], score_map)
		if beat:
			beat_list.append([float(rhythm_time) / len(beat), beat])
	return beat_list


def beat_parse(beats, score_map):
	beat = []
	brackets_end = 0
	num_end = 0
	# 遍历 '(ZGW) (BGW)' 或 '(-15+2) (-55+2)'中的字符
	for i in range(len(beats)):
		if i < brackets_end:
			pass
		elif num_end == 1:
			num_end = 0
		elif beats[i] == '(':
			brackets_end = beats.find(')', i) + 1
			single_beat = beat_num_parse(beats[i + 1: brackets_end - 1], score_map)
			beat.append(single_beat.lower())
		elif beats[i] == '-' or beats[i] == '+':
			single_beat = beat_num_parse(beats[i: i + 2], score_map)
			num_end = 1
			beat.append(single_beat.lower())
		else:
			single_beat = beat_num_parse(beats[i], score_map)
			beat.append(single_beat.lower())
	return beat


def beat_num_parse(num_str, score_map):
	single_word_index = 0
	single_word = []
	if ord(num_str[0]) > 64 or ord(num_str[0]) == 32:
		return num_str
	else:
		for i in range(len(num_str)):
			if single_word_index == 1:
				single_word_index = 0
			elif num_str[i] == '-' or num_str[i] == '+':
				single_word.append(score_map[num_str[i: i + 2]])
				single_word_index = 1
			else:
				single_word.append(score_map[num_str[i]])
		return ''.join(single_word)


def beat_play(beat_list, key_map):
	# 给出足够时间切换到乐器界面
	time.sleep(2)
	for rhy in beat_list:
		# rhy: ['0.5', ['gbk', 'sdf']]
		for beat in rhy[1]:
			# beat: 'gbk'
			for key in beat:
				# key: 'g'
				press_key(key_map[key])
				release_key(key_map[key])
			time.sleep(rhy[0])
		print('current rhythm:' + ','.join(rhy[1]))


if __name__ == '__main__':
	score_name = '江南.txt'
	score_rhythm = 0.6
	# main(score_name, score_rhythm)

	if is_admin():
		main(score_name, score_rhythm)
	else:
		# 强制以管理员身份运行
		ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
		# pass
