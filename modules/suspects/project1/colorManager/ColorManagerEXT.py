'''Info Header Start
Name : ColorManagerEXT
Author : kaegan@DESKTOP-6PU4AOJ
Version : 0
Build : 3
Savetimestamp : 2023-08-26T15:27:26.778372
Saveorigin : color_components.336.toe
Saveversion : 2022.33910
Info Header End'''
"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
import TDFunctions as TDF

from typing import List, Union

import numpy as np

class ColorManagerEXT:
	"""
	Test
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp
		self.color_prefix = 'Color'

	def CreateColorParams(self, num_colors: int):
		add_page = TDF.getCustomPage(self.ownerComp, 'Add')

		for par in add_page.pars:
			par.destroy()

		for idx in range(num_colors):
			add_page.appendStr(f'{self.color_prefix}{idx}', label=f'{self.color_prefix} {idx}')

		add_page.appendStr('Palettename', label='Palette Name').startSection = True
		add_page.appendPulse('Addpalette', label='Add Palette')

	def validate_hex_format(self, hex: str):
		if hex.startswith('#'):
			hex = hex.lstrip('#')

		match = re.search(r'(?:[A-Fa-f0-9]{6})', hex)

		if not match:                      
		  raise ValueError('Hex is not valid')
		return hex

	def hex_to_rgb(self, hex: str, alpha: int = 255, normalize: bool = True):
		try:
			# validate and convert hex to rgb tuple
			valid_hex = self.validate_hex_format(hex=hex)
			rgb = [int(valid_hex[i:i+2], 16) for i in (0, 2, 4)]
			rgba = rgb + [alpha]

			if normalize:
				rgba = [i / 255 for i in rgba]

		except ValueError as err:
			raise ValueError(f'Hex could not be validated or converted to rgb: {err}')

		return rgba

	def find_min_nodey(self, comp, **findChildrenKwargs):
		children_ops = comp.findChildren(**findChildrenKwargs)
		min_nodey = 0
		for op in children_ops:
			if op.nodeY < min_nodey:
				min_nodey = op.nodeY

		return min_nodey


	def find_color_positions(self, num_colors: int) -> List[float]:
		"""find the middle of each step for displaying color position in ramp correctly (nearest pixel).

		ex: if two colors [0.25, 0.5]
		ex: if five colors [0.1, 0.3, 0.5, 0.7, 0.9]
		"""
		step_value = 1.0 / num_colors
		steps = list(np.arange(0.0, 1.0, step_value))
		steps_plus_one = steps + [1.0]
		middle_steps = [(steps_plus_one[i + 1] + steps_plus_one[i]) / 2 for i in range(len(steps))]
		return middle_steps

	def clear_add_page(self, add_page_name: str = 'Add') -> None:
		add_page = TDF.getCustomPage(self.ownerComp, add_page_name)
		for par in add_page.pars:
			if par.isString:
				par.val = ''

	def AddPalette(
		self, 
		add_page_name: str = 'Add',
		internal_ramp_dat_name: str = 'ramp1_keys',
		nodey_difference: int = -150
	) -> None:
		add_page = TDF.getCustomPage(self.ownerComp, add_page_name)
		palette_name = self.ownerComp.par.Palettename.eval()
		num_colors = self.ownerComp.par.Numcolors.eval()

		new_palette_op = iop.colorPalettes.copy(iop.paletteTemplate, name=palette_name)
		new_palette_op.par.Resolutionw = num_colors

		rampDAT = new_palette_op.op(internal_ramp_dat_name)
		rampDAT.clear(keepFirstRow=True)

		color_positions = self.find_color_positions(num_colors)

		for idx, pos in enumerate(color_positions):
			color_hex = self.ownerComp.par[f'{self.color_prefix}{idx}'].eval()
			try:
				rgba_list = self.hex_to_rgb(color_hex)
				row = [pos] + rgba_list
				rampDAT.appendRow(row)
			except ValueError as err:
				print(f'Color hex: {color_hex} could not be added to palette. {err}')

		min_nodey = self.find_min_nodey(iop.colorPalettes)
		new_palette_op.nodeY = min_nodey + nodey_difference

		self.clear_add_page(add_page_name=add_page_name)

	def to_int_from_str(self, string_to_convert: str) -> Union[str, int]:
		if string_to_convert.isnumeric():
			try:
				string_to_convert = int(string_to_convert)
			except:
				print(
					'Palette name or index is numeric but could not be converted to int.'
				)
		return string_to_convert

	def ChangePalette(self, palette_name_or_idx: Union[str, int], fade_time: int = None):
		if fade_time is None:
			fade_time = self.ownerComp.par.Fadetime
		palette_name_or_idx = self.to_int_from_str(palette_name_or_idx)
		iop.sceneChanger.SceneChange(palette_name_or_idx, fadeTime=fade_time)


	def DeletePalette(self, palette_name_or_idx: Union[str, int]):
		scenesDAT = iop.sceneChanger.op('sceneIndex')

		# convert string to int if index passed as a string ie: '0'
		if isinstance(palette_name_or_idx, str):
			palette_name_or_idx = self.to_int_from_str(palette_name_or_idx)
	
		current_row = scenesDAT.row(palette_name_or_idx) 
		
		# if row is found, delete palette
		if current_row is not None:
			# should only ever be one row since names of operators must be unique
			# ie: palettes in the colorPalettes COMP must have unique names
			row_index = current_row[0].row

			# if deleteing current scene change to neighboring scene first
			if row_index == iop.sceneChanger.par.Currentscene:
				if row_index == 0:
					iop.sceneChanger.SceneChange(row_index + 1)
				else:
					iop.sceneChanger.SceneChange(row_index - 1)
			# if scene deleted is before the selected scene...
			elif row_index < iop.sceneChanger.par.Currentscene:
				iop.sceneChanger.SceneChange(iop.sceneChanger.par.Currentscene - 1)

			palette_name_to_delete = current_row[0].val
			operator_to_delete = iop.colorPalettes.op(palette_name_to_delete)
			operator_to_delete.destroy()
		else:
			print(
				f'Could not delete color palette name or index: {palette_name_or_idx} not found.'
			)

		