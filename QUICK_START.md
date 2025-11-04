# Quick Start Guide

## Testing the Scripts

All scripts are ready to use! Here are some quick examples:

### 1. Test Face Detection (Already Working)
```bash
python detect_faces.py
# Output: output_faces.jpg (8 faces detected)
```

### 2. Test Multi-Category Detection
```bash
python detect_objects.py your_image.jpg --categories "face,person,head" -o output_test.jpg
# Successfully detected 24 objects: 8 faces, 8 heads, 8 people
```

### 3. Try Other Detection Types

**Detect Objects by Category:**
```bash
python detect_objects.py your_image.jpg -c "person,face,hand"
```

**Detect Vehicles (need a different image):**
```bash
python detect_vehicles.py street_image.jpg
```

**Detect People with Body Parts:**
```bash
python detect_people.py your_image.jpg
```

**Point-Based Detection:**
```bash
python detect_with_points.py your_image.jpg -c "person"
```

**Find Specific Objects:**
```bash
python detect_specific.py your_image.jpg -d "the person on the left"
```

## What's Included

✅ **detect_faces.py** - Face detection (tested, working)
✅ **detect_objects.py** - Multi-category detection (tested, working)  
✅ **detect_vehicles.py** - Vehicle detection with attributes
✅ **detect_people.py** - People detection with body parts
✅ **detect_with_points.py** - Point-based grounding
✅ **detect_specific.py** - Description-based search
✅ **utils.py** - Shared visualization utilities
✅ **README.md** - Complete documentation

## Files Generated

- `output_faces.jpg` - Face detection results
- `output_test.jpg` - Multi-category detection test
- More outputs will be created as you run different scripts

## Next Steps

1. Try different images with the scripts
2. Experiment with different categories
3. Read README.md for detailed usage examples
4. Customize prompts in scripts for specific needs

Enjoy exploring Qwen3-VL's spatial understanding capabilities! 🎉
