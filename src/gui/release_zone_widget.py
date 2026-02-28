"""
Release Zone Interactive Widget for PyDebFlow.

Provides an interactive matplotlib canvas embedded in PyQt6 for marking
release zones on loaded terrain. Supports:
- Point mode: Click to place a circular release zone
- Polygon mode: Click to add vertices, right-click to close
- Manual coordinate entry via spinboxes
"""

import numpy as np
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
    QGroupBox, QButtonGroup, QRadioButton, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class ReleaseZoneWidget(QWidget):
    """
    Interactive widget for marking release zones on terrain.
    
    Embeds a matplotlib canvas showing the terrain hillshade/elevation
    and allows users to mark point or polygon release zones interactively.
    
    Signals:
        release_zone_changed(np.ndarray): Emitted when release zone is updated.
            The array is the release height field (same shape as terrain).
    """
    
    release_zone_changed = pyqtSignal(object)  # np.ndarray
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.terrain = None
        self.release_zone = None
        
        # Mode state
        self._mode = 'point'  # 'point' or 'polygon'
        
        # Point mode state
        self._point_marker = None  # (row, col)
        
        # Polygon mode state
        self._polygon_vertices = []  # list of (row, col)
        self._polygon_closed = False
        
        # Plot artists for overlay
        self._overlay_img = None
        self._marker_artists = []
        self._polygon_line = None
        self._polygon_fill = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Build the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # ── Top Row: Mode + Parameters (compact horizontal) ──
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        # Mode radios
        self.btn_group = QButtonGroup(self)
        
        self.radio_point = QRadioButton("🎯 Point")
        self.radio_point.setChecked(True)
        self.radio_point.setToolTip("Click on terrain to place a circular release zone")
        self.btn_group.addButton(self.radio_point)
        top_row.addWidget(self.radio_point)
        
        self.radio_polygon = QRadioButton("📐 Polygon")
        self.radio_polygon.setToolTip("Click to add vertices. Right-click to close polygon.")
        self.btn_group.addButton(self.radio_polygon)
        top_row.addWidget(self.radio_polygon)
        
        top_row.addSpacing(10)
        
        # Height
        top_row.addWidget(QLabel("H:"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(0.5, 100.0)
        self.height_spin.setValue(5.0)
        self.height_spin.setSingleStep(0.5)
        self.height_spin.setSuffix(" m")
        self.height_spin.setFixedWidth(90)
        top_row.addWidget(self.height_spin)
        
        # Radius
        top_row.addWidget(QLabel("R:"))
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 50)
        self.radius_spin.setValue(10)
        self.radius_spin.setToolTip("Radius for point mode")
        self.radius_spin.setFixedWidth(60)
        top_row.addWidget(self.radius_spin)
        
        top_row.addStretch()
        layout.addLayout(top_row)
        
        # ── Second Row: Manual Coordinate Entry (compact) ────
        manual_row = QHBoxLayout()
        manual_row.setSpacing(6)
        
        manual_row.addWidget(QLabel("Row:"))
        self.row_spin = QSpinBox()
        self.row_spin.setRange(0, 9999)
        self.row_spin.setValue(0)
        self.row_spin.setFixedWidth(70)
        manual_row.addWidget(self.row_spin)
        
        manual_row.addWidget(QLabel("Col:"))
        self.col_spin = QSpinBox()
        self.col_spin.setRange(0, 9999)
        self.col_spin.setValue(0)
        self.col_spin.setFixedWidth(70)
        manual_row.addWidget(self.col_spin)
        
        self.btn_add_point = QPushButton("➕ Add")
        self.btn_add_point.setToolTip(
            "Point mode: sets release center. Polygon mode: adds a vertex."
        )
        self.btn_add_point.setFixedWidth(70)
        manual_row.addWidget(self.btn_add_point)
        
        self.btn_close_polygon = QPushButton("✅ Close")
        self.btn_close_polygon.setToolTip("Close polygon and compute release zone")
        self.btn_close_polygon.setEnabled(False)
        self.btn_close_polygon.setFixedWidth(70)
        manual_row.addWidget(self.btn_close_polygon)
        
        manual_row.addStretch()
        
        self.status_label = QLabel("No terrain loaded")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        manual_row.addWidget(self.status_label)
        
        layout.addLayout(manual_row)
        
        # ── Matplotlib Canvas (takes all remaining space) ────
        self.figure = Figure(figsize=(6, 5), dpi=100, facecolor='#16213e')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(350)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1a1a2e')
        self.ax.set_title("Load terrain to begin", color='#e8e8e8', fontsize=10)
        self.ax.tick_params(colors='#888888', labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color('#3d3d5c')
        self.figure.tight_layout()
        layout.addWidget(self.canvas, stretch=1)
    
    def _connect_signals(self):
        """Wire up signals."""
        self.radio_point.toggled.connect(self._on_mode_changed)
        self.radio_polygon.toggled.connect(self._on_mode_changed)
        self.btn_add_point.clicked.connect(self._on_manual_add)
        self.btn_close_polygon.clicked.connect(self._on_close_polygon)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
    
    # ── Public API ──────────────────────────────────────────
    
    def set_terrain(self, terrain):
        """
        Set the terrain to display.
        
        Args:
            terrain: A Terrain instance with elevation, rows, cols, cell_size.
        """
        self.terrain = terrain
        self.release_zone = None
        self._point_marker = None
        self._polygon_vertices = []
        self._polygon_closed = False
        
        # Update spinbox ranges
        self.row_spin.setRange(0, terrain.rows - 1)
        self.col_spin.setRange(0, terrain.cols - 1)
        self.row_spin.setValue(terrain.rows // 5)
        self.col_spin.setValue(terrain.cols // 2)
        
        self._draw_terrain()
        self.status_label.setText("Click on terrain to mark release zone")
    
    def get_release_zone(self) -> Optional[np.ndarray]:
        """Return the current release zone array, or None if not set."""
        return self.release_zone
    
    def clear_zone(self):
        """Clear the current release zone."""
        self.release_zone = None
        self._point_marker = None
        self._polygon_vertices = []
        self._polygon_closed = False
        self.btn_close_polygon.setEnabled(False)
        
        if self.terrain is not None:
            self._draw_terrain()
            self.status_label.setText("Cleared — click to mark new zone")
        
        self.release_zone_changed.emit(None)
    
    # ── Internal: Drawing ───────────────────────────────────
    
    def _draw_terrain(self):
        """Redraw the terrain base image."""
        self.ax.clear()
        
        if self.terrain is None:
            self.ax.set_title("No terrain loaded", color='#e8e8e8', fontsize=10)
            self.canvas.draw_idle()
            return
        
        # Show hillshade
        hillshade = self.terrain.get_hillshade()
        self.ax.imshow(
            hillshade, cmap='gray', origin='upper',
            aspect='equal', interpolation='bilinear'
        )
        
        # Overlay elevation contours
        self.ax.contour(
            self.terrain.elevation, levels=15,
            colors='#00d9ff', linewidths=0.3, alpha=0.4
        )
        
        self.ax.set_title("Terrain — Click to mark release zone", color='#e8e8e8', fontsize=10)
        self.ax.set_xlabel("Column (j)", color='#888', fontsize=8)
        self.ax.set_ylabel("Row (i)", color='#888', fontsize=8)
        self.ax.tick_params(colors='#888888', labelsize=7)
        for spine in self.ax.spines.values():
            spine.set_color('#3d3d5c')
        
        # Redraw overlays if any
        self._draw_overlays()
        
        self.figure.tight_layout()
        self.canvas.draw_idle()
    
    def _draw_overlays(self):
        """Draw release zone overlays on top of terrain."""
        # Draw release zone heatmap
        if self.release_zone is not None:
            masked = np.ma.masked_where(self.release_zone < 0.01, self.release_zone)
            self.ax.imshow(
                masked, cmap='hot', alpha=0.55,
                origin='upper', aspect='equal', interpolation='bilinear'
            )
        
        # Draw point marker
        if self._point_marker is not None:
            r, c = self._point_marker
            radius = self.radius_spin.value()
            circle = plt_Circle(
                (c, r), radius,
                fill=False, edgecolor='#00ff88', linewidth=2, linestyle='--'
            )
            self.ax.add_patch(circle)
            self.ax.plot(c, r, 'x', color='#00ff88', markersize=10, markeredgewidth=2)
        
        # Draw polygon vertices/edges
        if self._polygon_vertices:
            verts = self._polygon_vertices
            rows = [v[0] for v in verts]
            cols = [v[1] for v in verts]
            
            # Plot vertices
            self.ax.plot(cols, rows, 'o', color='#ff6b6b', markersize=6, markeredgecolor='white', markeredgewidth=1)
            
            # Plot edges
            if len(verts) > 1:
                plot_cols = cols + ([cols[0]] if self._polygon_closed else [])
                plot_rows = rows + ([rows[0]] if self._polygon_closed else [])
                self.ax.plot(plot_cols, plot_rows, '-', color='#ff6b6b', linewidth=1.5)
            
            # Fill if closed
            if self._polygon_closed and len(verts) >= 3:
                from matplotlib.patches import Polygon as MplPolygon
                xy = np.array([[c, r] for r, c in verts])
                poly = MplPolygon(
                    xy, closed=True,
                    facecolor='#ff6b6b', alpha=0.2,
                    edgecolor='#ff6b6b', linewidth=2
                )
                self.ax.add_patch(poly)
    
    # ── Internal: Event Handlers ────────────────────────────
    
    def _on_mode_changed(self, checked):
        """Handle mode radio button toggle."""
        if not checked:
            return
        
        old_mode = self._mode
        self._mode = 'point' if self.radio_point.isChecked() else 'polygon'
        
        if old_mode != self._mode:
            # Clear current markers when switching modes
            self._point_marker = None
            self._polygon_vertices = []
            self._polygon_closed = False
            self.btn_close_polygon.setEnabled(False)
            
            if self._mode == 'point':
                self.radius_spin.setEnabled(True)
                self.status_label.setText("Point mode — click to place release center")
            else:
                self.radius_spin.setEnabled(False)
                self.status_label.setText("Polygon mode — click to add vertices, right-click to close")
            
            if self.terrain is not None:
                self._draw_terrain()
    
    def _on_canvas_click(self, event):
        """Handle mouse click on the matplotlib canvas."""
        if self.terrain is None:
            return
        if event.inaxes != self.ax:
            return
        
        col = int(round(event.xdata))
        row = int(round(event.ydata))
        
        # Clamp to terrain bounds
        row = max(0, min(row, self.terrain.rows - 1))
        col = max(0, min(col, self.terrain.cols - 1))
        
        if self._mode == 'point':
            self._place_point(row, col)
        elif self._mode == 'polygon':
            if event.button == 3:  # Right-click closes polygon
                self._close_polygon()
            else:
                self._add_polygon_vertex(row, col)
    
    def _on_manual_add(self):
        """Handle manual 'Add Point' button click."""
        if self.terrain is None:
            QMessageBox.warning(self, "No Terrain", "Load a DEM first.")
            return
        
        row = self.row_spin.value()
        col = self.col_spin.value()
        
        if self._mode == 'point':
            self._place_point(row, col)
        else:
            self._add_polygon_vertex(row, col)
    
    def _on_close_polygon(self):
        """Handle 'Close Polygon' button click."""
        self._close_polygon()
    
    # ── Internal: Release Zone Logic ────────────────────────
    
    def _place_point(self, row: int, col: int):
        """Place a point release zone at (row, col)."""
        self._point_marker = (row, col)
        
        height = self.height_spin.value()
        radius = self.radius_spin.value()
        
        self.release_zone = self.terrain.create_release_zone(
            center_i=row, center_j=col,
            radius=radius, height=height
        )
        
        self.status_label.setText(f"Point at ({row}, {col}) — r={radius}, h={height:.1f}m")
        self._draw_terrain()
        self.release_zone_changed.emit(self.release_zone)
    
    def _add_polygon_vertex(self, row: int, col: int):
        """Add a vertex to the polygon being drawn."""
        if self._polygon_closed:
            # Start a new polygon
            self._polygon_vertices = []
            self._polygon_closed = False
            self.release_zone = None
        
        self._polygon_vertices.append((row, col))
        n = len(self._polygon_vertices)
        
        self.btn_close_polygon.setEnabled(n >= 3)
        self.status_label.setText(
            f"Polygon: {n} vertices — "
            + ("right-click or Close to finish" if n >= 3 else f"need {3 - n} more")
        )
        
        self._draw_terrain()
    
    def _close_polygon(self):
        """Close the current polygon and compute the release zone."""
        if len(self._polygon_vertices) < 3:
            QMessageBox.warning(
                self, "Not Enough Vertices",
                "A polygon needs at least 3 vertices."
            )
            return
        
        self._polygon_closed = True
        height = self.height_spin.value()
        
        self.release_zone = self.terrain.create_polygon_release_zone(
            vertices=self._polygon_vertices,
            height=height,
            smooth=True
        )
        
        n = len(self._polygon_vertices)
        self.status_label.setText(f"Polygon ({n} vertices) — h={height:.1f}m ✓")
        self.btn_close_polygon.setEnabled(False)
        
        self._draw_terrain()
        self.release_zone_changed.emit(self.release_zone)


# Helper import for drawing circles (deferred to avoid import-time cost)
def plt_Circle(center, radius, **kwargs):
    """Create a matplotlib Circle patch."""
    from matplotlib.patches import Circle
    return Circle(center, radius, **kwargs)
