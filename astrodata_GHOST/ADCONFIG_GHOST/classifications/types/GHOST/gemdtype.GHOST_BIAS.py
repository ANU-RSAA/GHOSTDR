class GHOST_BIAS(DataClassification):
    name="GHOST_BIAS"
    usage = """
        Applies to all bias datasets from the GHOST instruments
        """
    parent = "GHOST"
    requirement = ISCLASS("GHOST") & PHU(OBSTYPE="BIAS")

newtypes.append(GHOST_BIAS())