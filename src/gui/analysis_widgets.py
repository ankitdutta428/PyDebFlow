"""
Analysis Widgets for PyDebFlow.

Provides RAMMS-style post-simulation analysis tools:
- Cross-Section Profile: draw a line on terrain, see elevation + flow profile
- Hydrograph: click a point, see flow height / discharge over time
"""

import numpy as np
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QPushButton, QSpinBox, QSplitter
)
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class CrossSectionWidget(QWidget):
    """
    RAMMS-style cross-section profile viewer.

    Click two points on the terrain map to define a transect line.
    The lower plot shows terrain elevation + flow height along that line,
    with a time slider to scrub through simulation timesteps.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.terrain = None
        self.outputs = None  # [(time, FlowState), ...]
        self._pt1 = None
        self._pt2 = None
        self._current_frame = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 2, 4, 2)

        # Instructions
        self.info_label = QLabel("Click two points on the terrain to define a cross-section line")
        self.info_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.info_label)

        # Splitter: top = terrain map, bottom = profile
        splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Top: Terrain Map ─────────────────────────────
        self.map_figure = Figure(figsize=(5, 3), dpi=100, facecolor='#16213e')
        self.map_canvas = FigureCanvas(self.map_figure)
        self.map_ax = self.map_figure.add_subplot(111)
        self.map_ax.set_facecolor('#1a1a2e')
        self.map_ax.set_title("Click two points for cross-section", color='#e8e8e8', fontsize=9)
        self._style_ax(self.map_ax)
        self.map_figure.tight_layout()
        self.map_canvas.mpl_connect('button_press_event', self._on_map_click)
        splitter.addWidget(self.map_canvas)

        # ── Bottom: Profile Plot ─────────────────────────
        self.profile_figure = Figure(figsize=(5, 2.5), dpi=100, facecolor='#16213e')
        self.profile_canvas = FigureCanvas(self.profile_figure)
        self.profile_ax = self.profile_figure.add_subplot(111)
        self.profile_ax.set_facecolor('#1a1a2e')
        self.profile_ax.set_title("Cross-Section Profile", color='#e8e8e8', fontsize=9)
        self._style_ax(self.profile_ax)
        self.profile_figure.tight_layout()
        splitter.addWidget(self.profile_canvas)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, stretch=1)

        # ── Time Slider ──────────────────────────────────
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Time:"))
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setMinimum(0)
        self.time_slider.setMaximum(0)
        self.time_slider.setValue(0)
        self.time_slider.valueChanged.connect(self._on_slider_changed)
        slider_row.addWidget(self.time_slider, stretch=1)
        self.time_label = QLabel("t = 0.0 s")
        self.time_label.setFixedWidth(100)
        slider_row.addWidget(self.time_label)

        self.btn_reset = QPushButton("🔄 Reset Line")
        self.btn_reset.setFixedWidth(90)
        self.btn_reset.clicked.connect(self._reset_line)
        slider_row.addWidget(self.btn_reset)

        layout.addLayout(slider_row)

    def set_data(self, terrain, outputs):
        """Load terrain and simulation outputs."""
        self.terrain = terrain
        self.outputs = outputs
        self._pt1 = None
        self._pt2 = None
        self._current_frame = 0

        if outputs:
            self.time_slider.setMaximum(len(outputs) - 1)
            self.time_slider.setValue(0)

        self._draw_map()

    # ── Drawing ──────────────────────────────────────────

    def _draw_map(self):
        """Draw the terrain map with cross-section line."""
        self.map_ax.clear()
        if self.terrain is None:
            self.map_canvas.draw_idle()
            return

        hillshade = self.terrain.get_hillshade()
        self.map_ax.imshow(hillshade, cmap='gray', origin='upper', aspect='equal')

        # Show flow overlay for current frame
        if self.outputs:
            t, state = self.outputs[self._current_frame]
            h = state.h_solid + state.h_fluid
            masked = np.ma.masked_where(h < 0.01, h)
            self.map_ax.imshow(masked, cmap='YlOrRd', alpha=0.5, origin='upper', aspect='equal')

        # Draw points and line
        if self._pt1 is not None:
            r, c = self._pt1
            self.map_ax.plot(c, r, 'o', color='#00ff88', markersize=8, markeredgecolor='white', markeredgewidth=1.5)
        if self._pt2 is not None:
            r, c = self._pt2
            self.map_ax.plot(c, r, 'o', color='#00ff88', markersize=8, markeredgecolor='white', markeredgewidth=1.5)
        if self._pt1 is not None and self._pt2 is not None:
            self.map_ax.plot(
                [self._pt1[1], self._pt2[1]], [self._pt1[0], self._pt2[0]],
                '--', color='#00ff88', linewidth=2
            )

        self.map_ax.set_title("Terrain — click two points for cross-section", color='#e8e8e8', fontsize=9)
        self._style_ax(self.map_ax)
        self.map_figure.tight_layout()
        self.map_canvas.draw_idle()

    def _draw_profile(self):
        """Draw the cross-section profile."""
        self.profile_ax.clear()

        if self._pt1 is None or self._pt2 is None or self.terrain is None:
            self.profile_ax.set_title("Select two points on the map above", color='#e8e8e8', fontsize=9)
            self._style_ax(self.profile_ax)
            self.profile_figure.tight_layout()
            self.profile_canvas.draw_idle()
            return

        # Sample along the line
        n_samples = 200
        r1, c1 = self._pt1
        r2, c2 = self._pt2
        rows_line = np.linspace(r1, r2, n_samples)
        cols_line = np.linspace(c1, c2, n_samples)

        # Distance along line in meters
        dist = np.sqrt(
            ((rows_line - r1) * self.terrain.cell_size) ** 2 +
            ((cols_line - c1) * self.terrain.cell_size) ** 2
        )

        # Sample terrain elevation
        ri = np.clip(np.round(rows_line).astype(int), 0, self.terrain.rows - 1)
        ci = np.clip(np.round(cols_line).astype(int), 0, self.terrain.cols - 1)
        elev = self.terrain.elevation[ri, ci]

        # Plot terrain
        self.profile_ax.fill_between(dist, elev.min() - 5, elev, color='#8B7355', alpha=0.4, label='_nolegend_')
        self.profile_ax.plot(dist, elev, '-', color='#8B7355', linewidth=2, label='Terrain')

        # Plot flow at current timestep
        if self.outputs:
            t, state = self.outputs[self._current_frame]
            h_total = (state.h_solid + state.h_fluid)[ri, ci]
            flow_surface = elev + h_total

            mask = h_total > 0.01
            if mask.any():
                self.profile_ax.fill_between(
                    dist, elev, flow_surface,
                    where=mask, color='#ff4444', alpha=0.5, label='_nolegend_'
                )
                self.profile_ax.plot(dist, flow_surface, '-', color='#ff4444', linewidth=1.5, label=f'Flow (t={t:.1f}s)')

        self.profile_ax.set_xlabel("Distance (m)", color='#aaa', fontsize=8)
        self.profile_ax.set_ylabel("Elevation (m)", color='#aaa', fontsize=8)
        self.profile_ax.set_title("Cross-Section Profile", color='#e8e8e8', fontsize=9)
        self.profile_ax.legend(loc='upper right', fontsize=7, facecolor='#2a2a4a', edgecolor='#555', labelcolor='#ddd')
        self._style_ax(self.profile_ax)
        self.profile_figure.tight_layout()
        self.profile_canvas.draw_idle()

    # ── Events ───────────────────────────────────────────

    def _on_map_click(self, event):
        if self.terrain is None or event.inaxes != self.map_ax:
            return
        col = int(round(event.xdata))
        row = int(round(event.ydata))
        row = max(0, min(row, self.terrain.rows - 1))
        col = max(0, min(col, self.terrain.cols - 1))

        if self._pt1 is None:
            self._pt1 = (row, col)
            self.info_label.setText(f"Point A: ({row}, {col}) — click second point")
        elif self._pt2 is None:
            self._pt2 = (row, col)
            length = np.sqrt(
                ((self._pt2[0] - self._pt1[0]) * self.terrain.cell_size) ** 2 +
                ((self._pt2[1] - self._pt1[1]) * self.terrain.cell_size) ** 2
            )
            self.info_label.setText(f"A({self._pt1[0]},{self._pt1[1]}) → B({self._pt2[0]},{self._pt2[1]}) | {length:.0f} m")
        else:
            # Reset and start new line
            self._pt1 = (row, col)
            self._pt2 = None
            self.info_label.setText(f"Point A: ({row}, {col}) — click second point")

        self._draw_map()
        self._draw_profile()

    def _on_slider_changed(self, value):
        self._current_frame = value
        if self.outputs and value < len(self.outputs):
            t = self.outputs[value][0]
            self.time_label.setText(f"t = {t:.1f} s")
        self._draw_map()
        self._draw_profile()

    def _reset_line(self):
        self._pt1 = None
        self._pt2 = None
        self.info_label.setText("Click two points on the terrain to define a cross-section line")
        self._draw_map()
        self._draw_profile()

    def _style_ax(self, ax):
        ax.tick_params(colors='#888', labelsize=7)
        for spine in ax.spines.values():
            spine.set_color('#3d3d5c')


class HydrographWidget(QWidget):
    """
    Hydrograph viewer — click a point on the terrain to see
    flow height, velocity, and discharge over time at that location.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.terrain = None
        self.outputs = None
        self._monitor_point = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 2, 4, 2)

        # Info
        self.info_label = QLabel("Click a point on the terrain to see hydrograph")
        self.info_label.setStyleSheet("color: #aaa; font-size: 11px;")
        layout.addWidget(self.info_label)

        # Manual entry row
        entry_row = QHBoxLayout()
        entry_row.addWidget(QLabel("Row:"))
        self.row_spin = QSpinBox()
        self.row_spin.setRange(0, 9999)
        self.row_spin.setFixedWidth(70)
        entry_row.addWidget(self.row_spin)
        entry_row.addWidget(QLabel("Col:"))
        self.col_spin = QSpinBox()
        self.col_spin.setRange(0, 9999)
        self.col_spin.setFixedWidth(70)
        entry_row.addWidget(self.col_spin)
        self.btn_set = QPushButton("📍 Set Point")
        self.btn_set.setFixedWidth(90)
        self.btn_set.clicked.connect(self._on_manual_set)
        entry_row.addWidget(self.btn_set)
        entry_row.addStretch()
        layout.addLayout(entry_row)

        # Splitter: top = terrain, bottom = hydrograph plots
        splitter = QSplitter(Qt.Orientation.Vertical)

        # ── Top: Terrain ─────────────────────────────────
        self.map_figure = Figure(figsize=(5, 2.5), dpi=100, facecolor='#16213e')
        self.map_canvas = FigureCanvas(self.map_figure)
        self.map_ax = self.map_figure.add_subplot(111)
        self.map_ax.set_facecolor('#1a1a2e')
        self._style_ax(self.map_ax)
        self.map_figure.tight_layout()
        self.map_canvas.mpl_connect('button_press_event', self._on_map_click)
        splitter.addWidget(self.map_canvas)

        # ── Bottom: Hydrograph Plots ─────────────────────
        self.hydro_figure = Figure(figsize=(5, 3), dpi=100, facecolor='#16213e')
        self.hydro_canvas = FigureCanvas(self.hydro_figure)
        self.ax_height = self.hydro_figure.add_subplot(211)
        self.ax_vel = self.hydro_figure.add_subplot(212)
        for ax in [self.ax_height, self.ax_vel]:
            ax.set_facecolor('#1a1a2e')
            self._style_ax(ax)
        self.hydro_figure.tight_layout()
        splitter.addWidget(self.hydro_canvas)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, stretch=1)

    def set_data(self, terrain, outputs):
        """Load terrain and simulation outputs."""
        self.terrain = terrain
        self.outputs = outputs
        self._monitor_point = None

        if terrain:
            self.row_spin.setRange(0, terrain.rows - 1)
            self.col_spin.setRange(0, terrain.cols - 1)
            self.row_spin.setValue(terrain.rows // 2)
            self.col_spin.setValue(terrain.cols // 2)

        self._draw_map()
        self._draw_hydrograph()

    # ── Drawing ──────────────────────────────────────────

    def _draw_map(self):
        self.map_ax.clear()
        if self.terrain is None:
            self.map_canvas.draw_idle()
            return

        hillshade = self.terrain.get_hillshade()
        self.map_ax.imshow(hillshade, cmap='gray', origin='upper', aspect='equal')

        # Show max flow extent
        if self.outputs:
            max_h = np.zeros((self.terrain.rows, self.terrain.cols))
            for _, state in self.outputs:
                max_h = np.maximum(max_h, state.h_solid + state.h_fluid)
            masked = np.ma.masked_where(max_h < 0.01, max_h)
            self.map_ax.imshow(masked, cmap='YlOrRd', alpha=0.4, origin='upper', aspect='equal')

        # Draw monitor point
        if self._monitor_point is not None:
            r, c = self._monitor_point
            self.map_ax.plot(c, r, 's', color='#00ccff', markersize=10,
                           markeredgecolor='white', markeredgewidth=2)
            self.map_ax.annotate(
                f'({r},{c})', (c, r), color='#00ccff', fontsize=8,
                xytext=(8, -8), textcoords='offset points'
            )

        self.map_ax.set_title("Click to place monitor point", color='#e8e8e8', fontsize=9)
        self._style_ax(self.map_ax)
        self.map_figure.tight_layout()
        self.map_canvas.draw_idle()

    def _draw_hydrograph(self):
        self.ax_height.clear()
        self.ax_vel.clear()

        if self._monitor_point is None or not self.outputs:
            self.ax_height.set_title("Select a monitor point", color='#e8e8e8', fontsize=9)
            self.ax_vel.set_title("", color='#e8e8e8', fontsize=9)
            for ax in [self.ax_height, self.ax_vel]:
                self._style_ax(ax)
            self.hydro_figure.tight_layout()
            self.hydro_canvas.draw_idle()
            return

        r, c = self._monitor_point
        times = []
        h_solid_series = []
        h_fluid_series = []
        h_total_series = []
        speed_s_series = []
        speed_f_series = []
        discharge_series = []

        for t, state in self.outputs:
            times.append(t)
            hs = state.h_solid[r, c]
            hf = state.h_fluid[r, c]
            h_solid_series.append(hs)
            h_fluid_series.append(hf)
            h_total_series.append(hs + hf)

            vs = np.sqrt(state.u_solid[r, c]**2 + state.v_solid[r, c]**2)
            vf = np.sqrt(state.u_fluid[r, c]**2 + state.v_fluid[r, c]**2)
            speed_s_series.append(vs)
            speed_f_series.append(vf)

            # Discharge = h * v * cell_width (per unit width)
            v_avg = (hs * vs + hf * vf) / max(hs + hf, 1e-6)
            discharge_series.append((hs + hf) * v_avg * self.terrain.cell_size)

        times = np.array(times)

        # ── Flow Height ──────────────────────────────────
        self.ax_height.fill_between(times, 0, h_solid_series, color='#cc6633', alpha=0.6, label='Solid')
        self.ax_height.fill_between(times, h_solid_series, h_total_series, color='#3399cc', alpha=0.6, label='Fluid')
        self.ax_height.plot(times, h_total_series, '-', color='white', linewidth=1, label='Total')
        self.ax_height.set_ylabel("Height (m)", color='#aaa', fontsize=8)
        self.ax_height.set_title(f"Hydrograph at ({r}, {c})", color='#e8e8e8', fontsize=9)
        self.ax_height.legend(loc='upper right', fontsize=6, facecolor='#2a2a4a', edgecolor='#555', labelcolor='#ddd')
        self._style_ax(self.ax_height)

        # ── Velocity / Discharge ─────────────────────────
        ax2 = self.ax_vel
        ax2.plot(times, speed_s_series, '-', color='#cc6633', linewidth=1.2, label='v_solid')
        ax2.plot(times, speed_f_series, '-', color='#3399cc', linewidth=1.2, label='v_fluid')
        ax2.set_ylabel("Velocity (m/s)", color='#aaa', fontsize=8)
        ax2.set_xlabel("Time (s)", color='#aaa', fontsize=8)

        # Discharge on secondary axis
        ax2r = ax2.twinx()
        ax2r.plot(times, discharge_series, '--', color='#ffcc00', linewidth=1, alpha=0.7, label='Q')
        ax2r.set_ylabel("Discharge (m³/s)", color='#ffcc00', fontsize=8)
        ax2r.tick_params(axis='y', colors='#ffcc00', labelsize=7)
        ax2r.spines['right'].set_color('#ffcc00')

        # Combined legend
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2r.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2,
                   loc='upper right', fontsize=6, facecolor='#2a2a4a', edgecolor='#555', labelcolor='#ddd')
        self._style_ax(ax2)

        self.hydro_figure.tight_layout()
        self.hydro_canvas.draw_idle()

    # ── Events ───────────────────────────────────────────

    def _on_map_click(self, event):
        if self.terrain is None or event.inaxes != self.map_ax:
            return
        col = int(round(event.xdata))
        row = int(round(event.ydata))
        row = max(0, min(row, self.terrain.rows - 1))
        col = max(0, min(col, self.terrain.cols - 1))

        self._monitor_point = (row, col)
        self.row_spin.setValue(row)
        self.col_spin.setValue(col)
        self.info_label.setText(f"Monitor point: ({row}, {col})")
        self._draw_map()
        self._draw_hydrograph()

    def _on_manual_set(self):
        if self.terrain is None:
            return
        row = self.row_spin.value()
        col = self.col_spin.value()
        self._monitor_point = (row, col)
        self.info_label.setText(f"Monitor point: ({row}, {col})")
        self._draw_map()
        self._draw_hydrograph()

    def _style_ax(self, ax):
        ax.tick_params(colors='#888', labelsize=7)
        for spine in ax.spines.values():
            spine.set_color('#3d3d5c')
