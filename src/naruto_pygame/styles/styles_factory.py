from .naruto_characters_style import HeadBandStyle, KakashiMaskStyle, KakashiHairStyle, TobiMaskStyle
from typing import List


class StyleFactory:
    @staticmethod
    def create_style(frame, style_name: List[str], holistic_results):
        if len(style_name) == 1:
            filename = style_name[0] 
            
            if filename.endswith("headband"):
                return HeadBandStyle(f"{filename}.png", holistic_results).apply(frame)
                
            if filename.endswith("hair") and not filename.endswith("headband"):
                return KakashiHairStyle(f"{filename}.png", holistic_results).apply(frame)
                
            if filename.endswith("mask") and not filename.endswith("fullfacemask"):
                return KakashiMaskStyle(f"{filename}.png", holistic_results).apply(frame)
                
            if filename.endswith("fullfacemask"):
                return TobiMaskStyle(f"{filename}.png", holistic_results).apply(frame)
                
        elif len(style_name) > 1:
            has_fullfacemask = any(s.endswith("fullfacemask") for s in style_name)
            has_headband = any(s.endswith("headband") for s in style_name)
            has_hair = any(s.endswith("hair") for s in style_name)
            has_mask = any(s.endswith("mask") and not s.endswith("fullfacemask") for s in style_name)

            if has_fullfacemask:
                return frame 
                
            if has_headband and has_hair:
                return frame 

            if has_headband and has_mask:
                filename_headband, filename_mask = None, None
                for style in style_name:
                    if style.endswith("headband"): 
                        filename_headband = style 
                    if style.endswith("mask") and not style.endswith("fullfacemask"): 
                        filename_mask = style
                
                if filename_headband and filename_mask:
                    frame = HeadBandStyle(f"{filename_headband}.png", holistic_results).apply(frame)
                    frame = KakashiMaskStyle(f"{filename_mask}.png", holistic_results).apply(frame)
                return frame

            if has_hair and has_mask:
                filename_hair, filename_mask = None, None
                for style in style_name:
                    if style.endswith("hair"):
                        filename_hair = style 
                    if style.endswith("mask") and not style.endswith("fullfacemask"): 
                        filename_mask = style
                        
                if filename_hair and filename_mask:
                    frame = KakashiHairStyle(f"{filename_hair}.png", holistic_results).apply(frame)
                    frame = KakashiMaskStyle(f"{filename_mask}.png", holistic_results).apply(frame)
                return frame

        return frame