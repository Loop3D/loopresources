# 1 - Desurveying Drillholes

Desurveying converts downhole survey measurements into 3D spatial coordinates along the drillhole path. This is critical for accurate subsurface modeling and resource estimation.

### **Assumptions**

*   **Azimuth**: Angle measured clockwise from **true north** (degrees).
*   **Dip**: Angle from **horizontal**, where **negative values indicate downward inclination**.
*   **Depth**: Measured along the drillhole from the collar.



### **Methods**

*   **Minimum Curvature**  
    Applied when more than two survey points exist. This method assumes a smooth arc between points, minimizing deviation from true curvature.
*   **Tangent Method**  
    Used when only two points exist (collar and one survey), assuming a straight line between them.

### **Resampling**

Drillhole paths can be resampled into smaller intervals for modelling or interpolation.

*   Loopresources uses **Slerp (Spherical Linear Interpolation)** to interpolate orientations smoothly between survey points, preserving directional accuracy.

***

Would you like me to **extend this with a code snippet showing how to call your desurvey function**, or **add a diagram illustrating azimuth/dip conventions and curvature vs tangent paths**?

