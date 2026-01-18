"""
PyDebFlow Main Window - PyQt6 GUI

Premium desktop application for debris flow simulation.
"""

import sys
import numpy as np
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QPushButton, QFileDialog,
    QSpinBox, QDoubleSpinBox, QComboBox, QProgressBar,
    QTextEdit, QSplitter, QTabWidget, QMessageBox,
    QStatusBar, QToolBar, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont


class SimulationWorker(QThread):
    """Background worker for running simulations."""
    
    progress = pyqtSignal(float, float, int)  # progress, time, step
    finished = pyqtSignal(object)  # outputs list
    error = pyqtSignal(str)
    
    def __init__(self, terrain, params, t_end):
        super().__init__()
        self.terrain = terrain
        self.params = params
        self.t_end = t_end
        self._is_cancelled = False
    
    def run(self):
        try:
            from src.core.flow_model import TwoPhaseFlowModel, FlowState, FlowParameters
            from src.core.noc_tvd_solver import NOCTVDSolver, SolverConfig
            
            # Setup model
            flow_params = FlowParameters(**self.params)
            model = TwoPhaseFlowModel(flow_params)
            config = SolverConfig(cfl_number=0.4, max_timestep=0.5)
            solver = NOCTVDSolver(self.terrain, model, config)
            
            # Initial state
            state = FlowState.zeros((self.terrain.rows, self.terrain.cols))
            release = self.terrain.create_release_zone(
                self.terrain.rows // 5,
                self.terrain.cols // 2,
                10, 5.0
            )
            state.h_solid = release * 0.7
            state.h_fluid = release * 0.3
            
            # Run with progress callback
            def callback(prog, t, step):
                if self._is_cancelled:
                    raise InterruptedError("Cancelled")
                self.progress.emit(prog, t, step)
            
            outputs = solver.run_simulation(
                state, self.t_end,
                output_interval=max(1.0, self.t_end / 60),
                progress_callback=callback
            )
            
            self.finished.emit(outputs)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def cancel(self):
        self._is_cancelled = True


class MainWindow(QMainWindow):
    """PyDebFlow main application window."""
    
    def __init__(self):
        super().__init__()
        self.terrain = None
        self.outputs = None
        self.worker = None
        
        self._setup_ui()
        self._create_menu()
        self._create_toolbar()
        self._apply_style()
    
    def _setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("PyDebFlow - Mass Flow Simulation")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        
        # Left panel - Controls
        left_panel = self._create_control_panel()
        
        # Right panel - Visualization
        right_panel = self._create_viz_panel()
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready - Load a DEM file to begin")
    
    def _create_control_panel(self) -> QWidget:
        """Create the left control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # DEM Loading
        dem_group = QGroupBox("📍 DEM / Terrain")
        dem_layout = QVBoxLayout(dem_group)
        
        self.dem_label = QLabel("No DEM loaded")
        self.dem_label.setWordWrap(True)
        dem_layout.addWidget(self.dem_label)
        
        btn_layout = QHBoxLayout()
        self.btn_load_dem = QPushButton("Load DEM...")
        self.btn_load_dem.clicked.connect(self._load_dem)
        btn_layout.addWidget(self.btn_load_dem)
        
        self.btn_synthetic = QPushButton("Synthetic")
        self.btn_synthetic.clicked.connect(self._create_synthetic)
        btn_layout.addWidget(self.btn_synthetic)
        dem_layout.addLayout(btn_layout)
        
        layout.addWidget(dem_group)
        
        # Flow Parameters
        params_group = QGroupBox("⚙️ Flow Parameters")
        params_layout = QGridLayout(params_group)
        
        # Preset
        params_layout.addWidget(QLabel("Preset:"), 0, 0)
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Debris Flow", "Snow Avalanche", "Lahar", "Rock Avalanche"])
        self.preset_combo.currentTextChanged.connect(self._apply_preset)
        params_layout.addWidget(self.preset_combo, 0, 1)
        
        # Density
        params_layout.addWidget(QLabel("Solid Density:"), 1, 0)
        self.density_spin = QSpinBox()
        self.density_spin.setRange(100, 5000)
        self.density_spin.setValue(2500)
        self.density_spin.setSuffix(" kg/m³")
        params_layout.addWidget(self.density_spin, 1, 1)
        
        # Friction
        params_layout.addWidget(QLabel("Friction Angle:"), 2, 0)
        self.friction_spin = QDoubleSpinBox()
        self.friction_spin.setRange(5, 45)
        self.friction_spin.setValue(22.0)
        self.friction_spin.setSuffix("°")
        params_layout.addWidget(self.friction_spin, 2, 1)
        
        # Voellmy mu
        params_layout.addWidget(QLabel("Voellmy μ:"), 3, 0)
        self.mu_spin = QDoubleSpinBox()
        self.mu_spin.setRange(0.01, 0.5)
        self.mu_spin.setValue(0.12)
        self.mu_spin.setSingleStep(0.01)
        params_layout.addWidget(self.mu_spin, 3, 1)
        
        # Voellmy xi
        params_layout.addWidget(QLabel("Voellmy ξ:"), 4, 0)
        self.xi_spin = QSpinBox()
        self.xi_spin.setRange(100, 3000)
        self.xi_spin.setValue(400)
        self.xi_spin.setSuffix(" m/s²")
        params_layout.addWidget(self.xi_spin, 4, 1)
        
        layout.addWidget(params_group)
        
        # Simulation
        sim_group = QGroupBox("▶️ Simulation")
        sim_layout = QVBoxLayout(sim_group)
        
        t_layout = QHBoxLayout()
        t_layout.addWidget(QLabel("Duration:"))
        self.time_spin = QSpinBox()
        self.time_spin.setRange(10, 600)
        self.time_spin.setValue(60)
        self.time_spin.setSuffix(" s")
        t_layout.addWidget(self.time_spin)
        sim_layout.addLayout(t_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        sim_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        sim_layout.addWidget(self.progress_label)
        
        btn_sim_layout = QHBoxLayout()
        self.btn_run = QPushButton("🚀 Run Simulation")
        self.btn_run.clicked.connect(self._run_simulation)
        self.btn_run.setEnabled(False)
        btn_sim_layout.addWidget(self.btn_run)
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self._cancel_simulation)
        self.btn_cancel.setEnabled(False)
        btn_sim_layout.addWidget(self.btn_cancel)
        sim_layout.addLayout(btn_sim_layout)
        
        layout.addWidget(sim_group)
        
        # Visualization
        viz_group = QGroupBox("🎨 Visualization")
        viz_layout = QVBoxLayout(viz_group)
        
        self.btn_view_3d = QPushButton("🌐 View 3D Animation")
        self.btn_view_3d.clicked.connect(self._show_3d_view)
        self.btn_view_3d.setEnabled(False)
        viz_layout.addWidget(self.btn_view_3d)
        
        self.btn_export_video = QPushButton("🎬 Export Video")
        self.btn_export_video.clicked.connect(self._export_video)
        self.btn_export_video.setEnabled(False)
        viz_layout.addWidget(self.btn_export_video)
        
        self.btn_export_results = QPushButton("💾 Export Results")
        self.btn_export_results.clicked.connect(self._export_results)
        self.btn_export_results.setEnabled(False)
        viz_layout.addWidget(self.btn_export_results)
        
        layout.addWidget(viz_group)
        
        # Spacer
        layout.addStretch()
        
        return panel
    
    def _create_viz_panel(self) -> QWidget:
        """Create visualization panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Tabs
        self.viz_tabs = QTabWidget()
        
        # Info tab
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        welcome = QLabel("""
        <h2>🏔️ PyDebFlow</h2>
        <p><b>Mass Flow Simulation Tool</b></p>
        <p>A premium r.avaflow/RAMMS-style debris flow simulator.</p>
        <hr>
        <h3>Quick Start:</h3>
        <ol>
            <li><b>Load DEM</b> - Click "Load DEM..." or use "Synthetic" for testing</li>
            <li><b>Configure</b> - Adjust flow parameters or use a preset</li>
            <li><b>Simulate</b> - Click "Run Simulation"</li>
            <li><b>Visualize</b> - View 3D animation or export video</li>
        </ol>
        <hr>
        <p><i>Supports GeoTIFF (.tif) and ESRI ASCII Grid (.asc) formats</i></p>
        """)
        welcome.setWordWrap(True)
        welcome.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(welcome)
        
        self.viz_tabs.addTab(info_widget, "ℹ️ Info")
        
        # Log tab
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.viz_tabs.addTab(self.log_text, "📋 Log")
        
        # Results tab
        self.results_label = QLabel("Run a simulation to see results here.")
        self.results_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_label.setWordWrap(True)
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        results_layout.addWidget(self.results_label)
        self.viz_tabs.addTab(results_widget, "📊 Results")
        
        layout.addWidget(self.viz_tabs)
        
        return panel
    
    def _create_menu(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open DEM...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._load_dem)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")
        
        run_action = QAction("&Run", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self._run_simulation)
        sim_menu.addAction(run_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """Create toolbar."""
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)
        
        toolbar.addAction("📂 Open", self._load_dem)
        toolbar.addAction("🏔️ Synthetic", self._create_synthetic)
        toolbar.addSeparator()
        toolbar.addAction("▶️ Run", self._run_simulation)
        toolbar.addSeparator()
        toolbar.addAction("🌐 3D View", self._show_3d_view)
    
    def _apply_style(self):
        """Apply premium dark theme styling."""
        self.setStyleSheet("""
            /* Main Window */
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: #1a1a2e;
                color: #e8e8e8;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #00d9ff;
                border: 1px solid #3d3d5c;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px 10px 10px 10px;
                background-color: #16213e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #00d9ff;
            }
            
            /* Labels */
            QLabel {
                color: #e8e8e8;
                font-size: 10px;
            }
            
            /* Primary Buttons */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:pressed {
                background: #5a4fcf;
            }
            QPushButton:disabled {
                background: #3d3d5c;
                color: #888;
            }
            
            /* Secondary Cancel Button */
            QPushButton#btn_cancel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #e74c3c, stop:1 #c0392b);
            }
            
            /* Progress Bar */
            QProgressBar {
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                text-align: center;
                background-color: #16213e;
                color: #fff;
                font-weight: bold;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00d9ff, stop:1 #667eea);
                border-radius: 5px;
            }
            
            /* Spin Boxes & Combo Boxes */
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #16213e;
                color: #fff;
                border: 1px solid #3d3d5c;
                border-radius: 4px;
                padding: 5px 8px;
                min-height: 20px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #00d9ff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #16213e;
                color: #fff;
                selection-background-color: #667eea;
            }
            
            /* Text Edit (Log) */
            QTextEdit {
                background-color: #0f0f1a;
                color: #00ff88;
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                padding: 8px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #3d3d5c;
                border-radius: 6px;
                background-color: #16213e;
            }
            QTabBar::tab {
                background-color: #1a1a2e;
                color: #888;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #16213e;
                color: #00d9ff;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                color: #fff;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #3d3d5c;
                width: 2px;
            }
            
            /* Menu Bar */
            QMenuBar {
                background-color: #0f0f1a;
                color: #e8e8e8;
                padding: 4px;
            }
            QMenuBar::item:selected {
                background-color: #667eea;
                border-radius: 4px;
            }
            QMenu {
                background-color: #16213e;
                color: #e8e8e8;
                border: 1px solid #3d3d5c;
            }
            QMenu::item:selected {
                background-color: #667eea;
            }
            
            /* Toolbar */
            QToolBar {
                background-color: #0f0f1a;
                border: none;
                spacing: 8px;
                padding: 4px;
            }
            QToolButton {
                background-color: transparent;
                color: #e8e8e8;
                padding: 6px 10px;
                border-radius: 4px;
            }
            QToolButton:hover {
                background-color: #3d3d5c;
            }
            
            /* Status Bar */
            QStatusBar {
                background-color: #0f0f1a;
                color: #00d9ff;
                font-size: 10px;
            }
            
            /* Scroll Bars */
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #3d3d5c;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #667eea;
            }
        """)
    
    def _log(self, message: str):
        """Add message to log."""
        self.log_text.append(message)
    
    def _load_dem(self):
        """Load DEM file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open DEM File",
            str(Path.home()),
            "DEM Files (*.tif *.tiff *.asc);;All Files (*.*)"
        )
        
        if filepath:
            try:
                from src.core.terrain import Terrain
                self.terrain = Terrain.load(filepath)
                
                self.dem_label.setText(
                    f"<b>{Path(filepath).name}</b><br>"
                    f"Size: {self.terrain.rows} × {self.terrain.cols}<br>"
                    f"Cell: {self.terrain.cell_size}m<br>"
                    f"Elev: {self.terrain.elevation.min():.0f} - {self.terrain.elevation.max():.0f}m"
                )
                
                self.btn_run.setEnabled(True)
                self._log(f"✓ Loaded: {filepath}")
                self.statusBar.showMessage(f"Loaded: {Path(filepath).name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load DEM:\n{e}")
    
    def _create_synthetic(self):
        """Create synthetic terrain."""
        from src.core.terrain import Terrain
        
        self.terrain = Terrain.create_synthetic(
            rows=80, cols=60, cell_size=10.0, slope_angle=25.0
        )
        
        self.dem_label.setText(
            "<b>Synthetic Terrain</b><br>"
            f"Size: 80 × 60<br>"
            f"Cell: 10m<br>"
            f"Slope: 25°"
        )
        
        self.btn_run.setEnabled(True)
        self._log("✓ Created synthetic terrain")
        self.statusBar.showMessage("Synthetic terrain created")
    
    def _apply_preset(self, preset: str):
        """Apply parameter preset."""
        presets = {
            "Debris Flow": (2500, 22.0, 0.12, 400),
            "Snow Avalanche": (300, 18.0, 0.15, 2000),
            "Lahar": (2700, 12.0, 0.08, 300),
            "Rock Avalanche": (2600, 28.0, 0.10, 500),
        }
        
        if preset in presets:
            density, friction, mu, xi = presets[preset]
            self.density_spin.setValue(density)
            self.friction_spin.setValue(friction)
            self.mu_spin.setValue(mu)
            self.xi_spin.setValue(xi)
            self._log(f"Applied preset: {preset}")
    
    def _run_simulation(self):
        """Run simulation."""
        if self.terrain is None:
            QMessageBox.warning(self, "No Terrain", "Please load a DEM first.")
            return
        
        params = {
            'solid_density': self.density_spin.value(),
            'fluid_density': 1100.0,
            'basal_friction_angle': self.friction_spin.value(),
            'voellmy_mu': self.mu_spin.value(),
            'voellmy_xi': self.xi_spin.value(),
        }
        
        self.worker = SimulationWorker(
            self.terrain, params, self.time_spin.value()
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        
        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        
        self._log(f"Starting simulation (t_end={self.time_spin.value()}s)...")
        self.worker.start()
    
    def _cancel_simulation(self):
        """Cancel running simulation."""
        if self.worker:
            self.worker.cancel()
            self._log("Cancelling...")
    
    def _on_progress(self, progress: float, time: float, step: int):
        """Handle progress update."""
        self.progress_bar.setValue(int(progress * 100))
        self.progress_label.setText(f"t = {time:.1f}s | step {step}")
    
    def _on_finished(self, outputs):
        """Handle simulation completion."""
        self.outputs = outputs
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.btn_view_3d.setEnabled(True)
        self.btn_export_video.setEnabled(True)
        self.btn_export_results.setEnabled(True)
        self.progress_bar.setValue(100)
        self.progress_label.setText("Complete!")
        
        self._log(f"✓ Simulation complete ({len(outputs)} frames)")
        self.statusBar.showMessage("Simulation complete!")
        
        # Update results
        if outputs:
            _, final = outputs[-1]
            max_h = max(s.h_solid.max() + s.h_fluid.max() for _, s in outputs)
            self.results_label.setText(
                f"<h3>Simulation Results</h3>"
                f"<p><b>Frames:</b> {len(outputs)}</p>"
                f"<p><b>Max flow height:</b> {max_h:.2f} m</p>"
                f"<p><b>Final volume:</b> {(final.h_solid.sum() + final.h_fluid.sum()) * self.terrain.cell_size**2:.0f} m³</p>"
            )
            self.viz_tabs.setCurrentIndex(2)  # Results tab
    
    def _on_error(self, error: str):
        """Handle simulation error."""
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self._log(f"✗ Error: {error}")
        QMessageBox.critical(self, "Simulation Error", error)
    
    def _show_3d_view(self):
        """Show 3D visualization."""
        if self.outputs is None:
            QMessageBox.warning(self, "No Results", "Run a simulation first.")
            return
        
        try:
            from src.visualization.dem_viewer import DEMViewer3D
            
            viewer = DEMViewer3D(self.terrain.elevation, self.terrain.cell_size)
            
            # Collect snapshots
            snapshots = [s.h_solid + s.h_fluid for _, s in self.outputs]
            times = [t for t, _ in self.outputs]
            
            viewer.load_snapshots(snapshots, times)
            
            # Show max height
            max_h = np.zeros_like(self.terrain.elevation)
            for snap in snapshots:
                max_h = np.maximum(max_h, snap)
            
            viewer.show_static(max_h, "PyDebFlow - 3D View")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"3D view failed:\n{e}")
    
    def _export_video(self):
        """Export animation video."""
        if self.outputs is None:
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Video", "debris_flow.mp4",
            "MP4 Video (*.mp4)"
        )
        
        if filepath:
            try:
                from src.visualization.dem_viewer import DEMViewer3D
                
                viewer = DEMViewer3D(self.terrain.elevation, self.terrain.cell_size)
                snapshots = [s.h_solid + s.h_fluid for _, s in self.outputs]
                times = [t for t, _ in self.outputs]
                viewer.load_snapshots(snapshots, times)
                
                viewer.export_animation(filepath)
                self._log(f"✓ Exported: {filepath}")
                QMessageBox.information(self, "Success", f"Video saved to:\n{filepath}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
    
    def _export_results(self):
        """Export results."""
        if self.outputs is None:
            return
        
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        
        if folder:
            try:
                from src.io.results import ResultsExporter, SimulationResults
                
                max_h = np.zeros_like(self.terrain.elevation)
                for _, s in self.outputs:
                    max_h = np.maximum(max_h, s.h_solid + s.h_fluid)
                
                _, final = self.outputs[-1]
                results = SimulationResults(
                    times=[t for t, _ in self.outputs],
                    max_flow_height=max_h,
                    final_h_solid=final.h_solid,
                    final_h_fluid=final.h_fluid,
                )
                
                metadata = {'cell_size': self.terrain.cell_size}
                exporter = ResultsExporter(folder, metadata)
                exported = exporter.export_results(results)
                
                self._log(f"✓ Exported to: {folder}")
                QMessageBox.information(self, "Success", f"Results saved to:\n{folder}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed:\n{e}")
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About PyDebFlow",
            "<h2>PyDebFlow</h2>"
            "<p><b>Mass Flow Simulation Tool</b></p>"
            "<p>Version 0.1.0</p>"
            "<hr>"
            "<p>A premium r.avaflow/RAMMS-style debris flow simulator.</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>Two-phase (solid+fluid) flow model</li>"
            "<li>NOC-TVD numerical solver</li>"
            "<li>Voellmy/Mohr-Coulomb rheology</li>"
            "<li>3D PyVista visualization</li>"
            "<li>GeoTIFF/ASCII Grid support</li>"
            "</ul>"
        )
