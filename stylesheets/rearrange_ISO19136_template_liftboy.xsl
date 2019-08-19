<?xml version="1.0" encoding="UTF-8"?>
<!-- 
    this stylesheet is specific to ISO 19136 metadata and shall be applied right after transform_ISO19136_template_liftboy.xsl
    Author: Cristiano Fugazza (fugazza.c@irea.cnr.it)
-->
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:output method="html" encoding="UTF-8" indent="yes" omit-xml-declaration="no"/>

    <xsl:strip-space elements="*" />
    
    <xsl:template match="/">
        <xsl:apply-templates select="node()"/>
    </xsl:template>
    
    <!-- capture the first instance of either keyw_voc_contr or keyw and then restore the correct ordering -->
    <xsl:template match="element">
        <xsl:choose>
            <xsl:when test="contains(id/text(), 'keyw_voc_contr') or contains(id/text(), 'keyw')">
                <xsl:if test="not( preceding::element[contains(id/text(), 'keyw') ] )">
                    <xsl:apply-templates select="//element[ contains(id/text(), 'keyw_voc_contr') ]" mode="rewrite" />
                    <xsl:apply-templates select="//element[ contains(id/text(), 'keyw') and not( contains(id/text(), 'keyw_voc_contr') ) ]" mode="rewrite" />
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:copy>
                    <xsl:apply-templates select="@* | node()"/>
                </xsl:copy>
            </xsl:otherwise>
        </xsl:choose>        
    </xsl:template>
    
    <!-- identity template -->
    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    <xsl:template match="@* | node()" mode="rewrite">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
