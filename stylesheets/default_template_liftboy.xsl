<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    this is the default stylesheet to be included in any Liftboy template 
    Author: Cristiano Fugazza (fugazza.c@irea.cnr.it)
-->
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="html" encoding="UTF-8" indent="yes" omit-xml-declaration="no"/>
    
    <xsl:strip-space elements="*" />

    <xsl:template match="/">
        <xsl:apply-templates select="node()"/>
    </xsl:template>

    <!-- check whether baseDocument can be omitted -->
    <xsl:template match="baseDocument" />
        
    <!-- wrap content of element baseDocument in a CDATA section
    <xsl:template match="baseDocument">
        <baseDocument>
            <xsl:text disable-output-escaping="yes">&lt;![CDATA[</xsl:text>
            <xsl:value-of select="text()" disable-output-escaping="yes"/>
            <xsl:text disable-output-escaping="yes">]]&gt;</xsl:text>
        </baseDocument>
    </xsl:template> -->
    
    <!-- unescape the values of elements path, value, labelValue, codeValue, fileUri, and root that may be double-escaped -->
    <xsl:template match="path/text()|value/text()|labelValue/text()|codeValue/text()|fileUri/text()|root/text()">
        <!-- <xsl:value-of select="." disable-output-escaping="no"/> -->
        <xsl:value-of select="." disable-output-escaping="yes"/>
    </xsl:template>

    <!-- remove elements defaultValue and hasValue -->
    <xsl:template match="defaultValue"/>
    <xsl:template match="hasValue"/>

    <!-- identity template -->
    <xsl:template match="@* | *">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
