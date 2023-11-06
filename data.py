from typing import List
import numpy as np
from dataclasses import dataclass
from constants import MarkerStyles, LineStyles

@dataclass
class Marker:
    style: MarkerStyles
    color: str
    size: float
    auto_color: bool = True

    def to_dict(self):
        return {
            "style": self.style.name,
            "color": self.color,
            "size": self.size,
            "auto_color": self.auto_color,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            style=MarkerStyles(d["style"]),
            color=d["color"],
            size=d["size"],
            auto_color=d["auto_color"],
        )

@dataclass
class Line:
    style: LineStyles
    color: str
    width: float
    auto_color: bool = True

    def to_dict(self):
        return {
            "style": self.style.name,
            "color": self.color,
            "width": self.width,
            "auto_color": self.auto_color,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            style=LineStyles(d["style"]),
            color=d["color"],
            width=d["width"],
            auto_color=d["auto_color"],
        )
    
@dataclass
class LegendEntry:
    show: bool
    label: str

    def to_dict(self):
        return {
            "show": self.show,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            label=d["label"],
        )

@dataclass
class LineOfBestFit:
    show: bool
    line: Line
    fit_type: str
    fit_params: List[float]
    legend_entry: LegendEntry
    auto_color: bool = True

    def to_dict(self):
        return {
            "show": self.show,
            "color": self.color,
            "width": self.width,
            "fit_Type": self.fit_type,
            "fit_params": self.fit_params,
            "auto_color": self.auto_color,
            "legend_entry": self.legend_entry.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            color=d["color"],
            width=d["width"],
            fit_Type=d["fit_Type"],
            fit_params=d["fit_params"],
            auto_color=d["auto_color"],
            legend_entry=LegendEntry.from_dict(d["legend_entry"]),
        )

@dataclass
class DataSeries:
    name: str
    x: np.array
    y: np.array
    marker: Marker
    line: Line
    legend_entry: LegendEntry
    line_of_best_fit: LineOfBestFit

    @property
    def data(self):
        return np.array([self.x, self.y]).T
    
    def to_dict(self):
        return {
            "name": self.name,
            "x": self.x.tolist(),
            "y": self.y.tolist(),
            "marker": self.marker.to_dict(),
            "line": self.line.to_dict(),
            "legend_entry": self.legend_entry.to_dict(),
            "line_of_best_fit": self.line_of_best_fit.to_dict(),
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            name=d["name"],
            x=np.array(d["x"]),
            y=np.array(d["y"]),
            marker=Marker.from_dict(d["marker"]),
            line=Line.from_dict(d["line"]),
            legend_entry=LegendEntry.from_dict(d["legend_entry"]),
            line_of_best_fit=LineOfBestFit.from_dict(d["line_of_best_fit"]),
        )

@dataclass
class AxisProperties:
    min: float | None
    max: float | None
    label: str
    font_size: int

    def to_dict(self):
        return {
            "min": self.min,
            "max": self.max,
            "label": self.label,
            "font_size": self.font_size,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            min=d["min"],
            max=d["max"],
            label=d["label"],
            font_size=d["font_size"],
        )

@dataclass
class TitleProperties:
    text: str
    font_size: int

    def to_dict(self):
        return {
            "text": self.text,
            "font_size": self.font_size,
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            text=d["text"],
            font_size=d["font_size"],
        )

@dataclass
class LegendProperties:
    show: bool
    position: str
    font_size: float
    background_color: str
    opacity: float
    auto_color: bool = True

    def to_dict(self):
        return {
            "show": self.show,
            "position": self.position,
            "font_size": self.font_size,
            "background_color": self.background_color,
            "opacity": self.opacity,
            "auto_color": self.auto_color,
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            show=d["show"],
            position=d["position"],
            font_size=d["font_size"],
            color=d["background_color"],
            opacity=d["opacity"],
            auto_color=d["auto_color"],
        )


@dataclass
class FigureProperties:
    x_axis: AxisProperties
    y_axis: AxisProperties
    title: TitleProperties
    legend: LegendProperties
    filename: str
    file_type: str
    theme: str

    def to_dict(self):
        return {
            "x_axis": self.x_axis.to_dict(),
            "y_axis": self.y_axis.to_dict(),
            "title": self.title.to_dict(),
            "legend": self.legend.to_dict(),
            "filename": self.filename,
            "file_type": self.file_type,
            "theme": self.theme,
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            x_axis=AxisProperties.from_dict(d["x_axis"]),
            y_axis=AxisProperties.from_dict(d["y_axis"]),
            title=TitleProperties.from_dict(d["title"]),
            legend=LegendProperties.from_dict(d["legend"]),
            filename=d["filename"],
            file_type=d["file_type"],
            theme=d["theme"],
        )

    @classmethod
    def default(cls):
        x_axis = AxisProperties(
            None,
            None,
            "$x$",
            14
        )
        y_axis = AxisProperties(
            None,
            None,
            "$y$",
            14
        )
        title = TitleProperties(
            "Title",
            16
        )
        legend = LegendProperties(
            True,
            "Best",
            14,
            "#ffffff",
            1.0,
        )
        filename = "figure"
        file_type = "pdf"
        return cls(
            x_axis=x_axis,
            y_axis=y_axis,
            title=title,
            legend=legend,
            filename=filename,
            file_type=file_type,
            theme="Newcastle",
        )
