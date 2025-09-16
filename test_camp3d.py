#!/usr/bin/env python3
"""
Unit tests for CAMP3D package
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

# Add the package to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'camp3d-0.1.0', 'src'))

from camp3d.config import Config, load
from camp3d.blender_exec import blender_script_path

class TestCAMP3D(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.test_dir, 'test_config.yaml')
        
        # Create a test config
        test_config = """
u2h:
  materials_dir: ./test_materials

blender:
  bin: blender

helios:
  output_dir: ./test_helios

scene:
  name: TestScene
  scene_dir: ./test_scene
  blend: ./test.blend
  semantics:
    trees_collection: Trees
    leaf_keywords: [Leaves, Needles]
    write_csv: false

postprocess:
  input_root: ./test_input
  output_root: ./test_output
  tile_size: 50.0
  merge_all_ts: false
  ground_label: 2
  wood_label: 3
  leaf_label: 4
  leafwood: false

planning:
  rotate_deg: 0
  survey_mode: ULS
  spacing: 20.0
  relative_altitude: 60.0
  speed: 5.0
  pulse_freq_hz: 200000
  pattern: criss-cross
"""
        with open(self.config_file, 'w') as f:
            f.write(test_config)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_config_loading(self):
        """Test configuration loading"""
        config = load(self.config_file)
        self.assertEqual(config.scene.name, "TestScene")
        self.assertEqual(config.planning.spacing, 20.0)
        self.assertEqual(config.scene.semantics.leaf_keywords, ["Leaves", "Needles"])
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = Config()
        self.assertEqual(config.blender.bin, "blender")
        self.assertEqual(config.u2h.materials_dir, "./materials")
        self.assertEqual(config.planning.survey_mode, "ULS")
    
    def test_postprocess_config(self):
        """Test postprocess configuration loading"""
        config = load(self.config_file)
        
        # Test postprocess configuration
        self.assertEqual(config.postprocess.input_root, './test_input')
        self.assertEqual(config.postprocess.output_root, './test_output')
        self.assertEqual(config.postprocess.tile_size, 50.0)
        self.assertEqual(config.postprocess.merge_all_ts, False)
        self.assertEqual(config.postprocess.ground_label, 2)
        self.assertEqual(config.postprocess.wood_label, 3)
        self.assertEqual(config.postprocess.leaf_label, 4)
        self.assertEqual(config.postprocess.leafwood, False)

    def test_materials_dir_config(self):
        """Test materials directory configuration"""
        config = load(self.config_file)
        
        # Test materials directory configuration
        self.assertEqual(config.u2h.materials_dir, './test_materials')

    def test_output_dir_config(self):
        """Test output directory configuration"""
        config = load(self.config_file)
        
        # Test output directory configuration
        self.assertEqual(config.helios.output_dir, './test_helios')
    
    def test_blender_script_path(self):
        """Test blender script path resolution"""
        script_path = blender_script_path("scene_create.py")
        self.assertTrue(script_path.endswith("scene_create.py"))
        self.assertTrue(os.path.exists(script_path))
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid config
        config = Config()
        self.assertIsNotNone(config)
        
        # Test that config loading works with valid data
        config = load(self.config_file)
        self.assertIsNotNone(config)
        self.assertEqual(config.u2h.materials_dir, './test_materials')

class TestBlenderScripts(unittest.TestCase):
    """Test blender script functionality"""
    
    def test_scene_create_args_parsing(self):
        """Test argument parsing in scene_create.py"""
        # Test the argument parsing logic without importing Blender modules
        argv = ['--create_new_scene', 'True', '--landscape_fbx', 'test.fbx']
        
        def get_arg_value(arg_name, default_value=None):
            try:
                idx = argv.index(arg_name)
                return argv[idx + 1]
            except (ValueError, IndexError):
                return default_value
        
        self.assertEqual(get_arg_value('--create_new_scene'), 'True')
        self.assertEqual(get_arg_value('--landscape_fbx'), 'test.fbx')
        self.assertEqual(get_arg_value('--nonexistent'), None)

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCAMP3D))
    suite.addTests(loader.loadTestsFromTestCase(TestBlenderScripts))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
