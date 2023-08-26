'''Info Header Start
Name : ColorMapperEXT
Author : kaegan@DESKTOP-6PU4AOJ
Version : 0
Build : 3
Savetimestamp : 2023-08-26T15:27:28.101568
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

from typing import List

class ColorMapperEXT:
	"""
	colorMapperEXT description
	"""
	def __init__(self, ownerComp):
		# The component to which this extension is attached
		self.ownerComp = ownerComp

	@property
	def InputNumColors(self):
		return iop.colorData.numRows - 1

	@property
	def ArtworkCOMP(self):
		return self.ownerComp.par.Artworkcomp.eval()

	@property
	def ColorChannelPage(self):
		return TDF.getCustomPage(self.ownerComp, 'Color Channels')
		
	def CreateColorChannelParams(self):
		for par in self.ColorChannelPage.pars:
			par.destroy()

		num_colors = self.InputNumColors
		for idx, row in enumerate(iop.artworkColorChannels.rows()):
			if row != []:
				par_label = row[0].val
				par_group_name = row[1].val

				# create int param
				new_param = self.ColorChannelPage.appendInt(par_group_name, label=par_label)
				new_param.min = 0
				new_param.normMin = 0
				new_param.clampMin = True

				new_param.max = num_colors
				new_param.normMax = num_colors
				new_param.clampMax = True
				if idx <= num_colors:
					new_param.default = idx
					new_param.val = idx
				else:
					new_param.default = num_colors
					new_param.val = num_colors

				# create toggle param
				toggle_name = f'{par_group_name}toggle'
				toggle_label = f'{par_label} Toggle'
				new_param = self.ColorChannelPage.appendToggle(toggle_name, label=toggle_label)

	def get_rgba_from_pargroup(self, parGroup) -> List[float]:
		return [par.eval() for par in parGroup.pars()]

	def SaveColorChannelDefaults(self, node_y_spacing: int = -150):
		# delete all existing default dats
		for op in iop.colorChannelDefaults.findChildren():
			op.destroy()

		# create new default dats
		nodeY = node_y_spacing
		for row in iop.artworkColorChannels.rows():
			pargroup_name = row[1]

			# create default dats name=par_group
			currentDAT = iop.colorChannelDefaults.create('tableDAT', pargroup_name)
			currentDAT.nodeY = nodeY
			nodeY += node_y_spacing

			# get param rgba for each channel in artwork comp
			current_par_group = self.ArtworkCOMP.parGroup[pargroup_name]
			rgba = self.get_rgba_from_pargroup(current_par_group)
			currentDAT.replaceRow(0, ['r', 'g', 'b', 'a'])
			currentDAT.appendRow(rgba)

	def ChangeArtworkColor(self, pargroup_name: str, colorDAT, color_channel_value: int):
		current_par_group = self.ArtworkCOMP.parGroup[pargroup_name]
		col_list = ['r', 'g', 'b', 'a']
		index = color_channel_value + 1
		rgba = [float(colorDAT[index, col].val) for col in col_list]
		
		for idx, par in enumerate(current_par_group.pars()):
			op.tweener.CreateTween(	
				par, 
				rgba[idx], 
				parent.ColorMapper.par.Fadetime,
			)

	def ChangeAllOpenColorChannels(self, colorDAT):
		for row in iop.artworkColorChannels.rows():
			par_group_name = row[1].val
			color_channel_int_par = parent.ColorMapper.par[par_group_name]
			color_channel_toggle_par = parent.ColorMapper.par[f'{par_group_name}toggle']

			# change only if channel open
			if color_channel_toggle_par.eval() == 1:
				self.ChangeArtworkColor(
						par_group_name,
						colorDAT,
						color_channel_value=color_channel_int_par.eval()
					)


	def ToggleAllChannels(self, value: int):
		for par in self.ColorChannelPage.pars:
			if par.isToggle:
				par.val = value







