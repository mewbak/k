// Copyright (C) 2014 K Team. All Rights Reserved.
package org.kframework.parser;

import com.beust.jcommander.Parameter;

public final class ExperimentalParserOptions {

    @Parameter(names="--fast-kast", description="Using the (experimental) faster C SDF parser.")
    public boolean fastKast = false;
}