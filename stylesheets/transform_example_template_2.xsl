<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes" omit-xml-declaration="no" />

<!-- identity template without namespace nodes
<xsl:template match="*">
    <xsl:element name="{local-name()}">
        <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*|text()|comment()|processing-instruction()">
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
</xsl:template> -->
    
<xsl:template match="/">
    <xsl:apply-templates select="@*|node()"/>
    <!-- <xsl:comment>PERFORMING XSLT TRANSFORMATION</xsl:comment> -->
</xsl:template>

<xsl:template match="defaultValue" />
<xsl:template match="hasValue" />

<!-- identity template -->
<xsl:template match="@*|node()">
    <xsl:copy>
        <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
</xsl:template>
</xsl:stylesheet>
