# coding=utf-8
#############################
#  Multitasking experiment: Typing digits (keyboard) while tracking (joystick)
#  Developed by Dietmar Sach (dsach@mail.de) for the Institute of Sport Science of the University of Augsburg
#  Based on a script made by Christian P. Janssen, c.janssen@ucl.ac.uk December 2009 - March 2010
#############################
import csv
import datetime
import inspect
import math
import os
import random
import time
import traceback
from enum import Enum
from os import path
from tkinter import *

import pygame
import scipy
import scipy.special


class TaskTypes(Enum):
    """
    Used to represent different task types.
    Do not modify anything here!
    """
    SingleTracking = 1
    SingleTyping = 2
    DualTask = 3
    PracticeSingleTracking = 4
    PracticeSingleTyping = 5
    PracticeDualTask = 6


class Penalty(Enum):
    """
    Used to represent different penalties.
    Do not modify anything here!
    """
    NoPenalty = 1  # Do not change the score
    LoseAll = 2
    LoseHalf = 3
    LoseAmount = 4 # Lose an amount specified in RuntimeVariables.PenaltyAmount


class Block:
    """
    Used to represent a block of trials.
    Do not modify anything here!
    """
    TaskType = None
    NumberOfTrials = 0

    def __init__(self, taskType, numberOfTrials):
        self.TaskType = taskType
        self.NumberOfTrials = numberOfTrials


class Circle:
    """
    Used to represent a circle.
    Do not modify anything here!
    """
    Radius = 0
    TypingTaskNumbersDualTask = ""
    InnerCircleColor = (255, 204, 102)  # orange
    BorderColor = (255, 0, 0)  # red

    def __init__(self, radius, typingTaskNumbersDualTask, innerCircleColor, borderColor):
        self.Radius = radius
        self.TypingTaskNumbersDualTask = typingTaskNumbersDualTask
        self.InnerCircleColor = innerCircleColor
        self.BorderColor = borderColor


class Vector2D:
    """
    Used to represent coordinates or measures with x and y.
    Do not modify anything here!
    """
    X = 0
    Y = 0

    def __init__(self, x, y):
        self.X = x
        self.Y = y


class ExperimentSettings:
    """
    These settings can be modified by the Experiment supervisor
    """
    CircleBorderThickness = 5
    SingleTypingTaskNumbers = "123"
    SingleTypingTaskNumbersLength = 27

    MaxTrialTimeDual = 90  # maximum time for dual-task trials
    MaxTrialTimeSingleTracking = 10  # maximum time for single-task tracking
    MaxTrialTimeSingleTyping = 20  # maximum time for single-task typing

    TaskWindowSize = Vector2D(550, 550)
    SpaceBetweenWindows = 128

    # Settings used for displaying Typing Task within Cursor
    GeneralFontSize = 30
    FontSizeTypingTaskNumberSingleTask = 30
    FontSizeTypingTaskNumberWithinCursor = 30
    FontColorTypingTaskNumberWithinCursor = (255, 255, 255)
    CursorSize = Vector2D(20, 20)
    CursorColorInside = (255, 0, 0)  # red
    CursorColorOutside = (0, 0, 255)  # blue

    # General settings
    CursorNoises = {"high": 5, "medium": 4, "low": 3}  # This is the speed of the cursor movement (standard deviation of noise)
    TimeFeedbackIsGiven = 4
    TimeFeedbackIsShown = 4
    BackgroundColorTaskWindows = (255, 255, 255)  # white
    BackgroundColorEntireScreen = (50, 50, 50)  # gray
    CoverColor = (200, 200, 200)  # very light gray
    Fullscreen = True

    # Practice trials settings
    CursorNoisePracticeTrials = CursorNoises["high"]
    PenaltyPracticeTrials = Penalty.NoPenalty


class Constants:
    Title = "Multitasking 3.0"
    ExperimentWindowSize = Vector2D(1280, 1024)
    OffsetLeftRight = int((ExperimentWindowSize.X - ExperimentSettings.SpaceBetweenWindows - 2 * ExperimentSettings.TaskWindowSize.X) / 2)
    TopLeftCornerOfTypingTaskWindow = Vector2D(OffsetLeftRight, 50)
    TopLeftCornerOfTrackingTaskWindow = Vector2D(OffsetLeftRight + ExperimentSettings.TaskWindowSize.X + ExperimentSettings.SpaceBetweenWindows, 50)
    TrackingWindowMiddleX = TopLeftCornerOfTrackingTaskWindow.X + int(ExperimentSettings.TaskWindowSize.X / 2.0)
    TrackingWindowMiddleY = TopLeftCornerOfTrackingTaskWindow.Y + int(ExperimentSettings.TaskWindowSize.Y / 2.0)
    ScalingJoystickAxis = 5  # how many pixels the cursor moves when joystick is at full angle (value of 1 or -1).
    StepSizeOfTrackingScreenUpdate = 0.005  # how many seconds does it take for a screen update
    SettingsFilename = "guiconfig.dat"


class RuntimeVariables:
    """
    These variables are managed by the program itself.
    Do not modify anything here!
    """
    BlockNumber = 0
    CirclesSmall = []
    CirclesBig = []
    CirclesPractice = []
    CurrentCircles = []  # is set for each condition
    CurrentTypingTaskNumbers = ""
    CurrentTypingTaskNumbersLength = 1
    CurrentTask = None
    CurrentCursorColor = ExperimentSettings.CursorColorInside
    CorrectlyTypedDigitsVisit = 0
    CurrentCondition = ""
    CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)
    CursorDistancesToMiddle = []
    DictTrialListEntries = {}
    DigitPressTimes = []
    DisableCorrectTypingScoreOutsideCircle = False
    DisplayTypingTaskWithinCursor = False
    EnteredDigitsStr = ""
    EnvironmentIsRunning = False
    GainCorrectDigit = 0
    GainIncorrectDigit = 5
    IncorrectlyTypedDigitsTrial = 0
    IncorrectlyTypedDigitsVisit = 0
    JoystickAxis = Vector2D(0, 0)  # the motion of the joystick
    JoystickObject = None
    LengthOfPathTracked = 0
    NumberOfCircleExits = 0
    OutputDataFile = None
    OutputDataFileTrialEnd = None
    ParallelDualTasks = False
    Penalty = None
    PenaltyAmount = 0
    RunningOrder = []
    RunPracticeTrials = True
    ShowPenaltyRewardNoise = True
    ScoresForPayment = []
    Screen = None
    StandardDeviationOfNoise = None
    StartTimeCurrentTrial = time.time()
    StartTimeOfFirstExperiment = time.time()
    ParticipantNumber = "0"
    TrackingTaskPresent = False
    TrackingWindowEntryCounter = 0
    TrackingWindowVisible = False
    TrialNumber = 0
    TrialScore = 0
    TypingTaskPresent = False
    TypingWindowEntryCounter = 0
    TypingWindowVisible = False
    VisitEndTime = 0
    VisitScore = 0
    VisitStartTime = 0
    WasCursorOutsideRadiusBefore = False


def calculateRmse(clearDistances):
    """
    The distances are collected each time the cursor changes its position.
    The distances are collected until the RMSE is calculated.
    The RMSE is calculated every time the data file is written.
    The distances are cleared if the parameter is set to True
    """
    n = len(RuntimeVariables.CursorDistancesToMiddle)
    if n == 0:
        return 0
    square = 0

    # Calculate square
    for i in range(0, n):
        square += (RuntimeVariables.CursorDistancesToMiddle[i] ** 2)

    if clearDistances:
        RuntimeVariables.CursorDistancesToMiddle = []

    # Calculate Mean
    mean = (square / float(n))
    # Calculate Root
    root = math.sqrt(mean)
    return root


def checkMouseClicked():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quitApp()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            posString = str(pos[0]) + "_" + str(pos[1])
            writeOutputDataFile("MousePressed", posString)
            return pos[0], pos[1]
    return False


def checkKeyPressed():
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and RuntimeVariables.TrackingWindowVisible:
            pos = pygame.mouse.get_pos()
            RuntimeVariables.CursorCoordinates = Vector2D(pos[0], pos[1])
        elif event.type == pygame.QUIT:
            quitApp()
        elif event.type == pygame.JOYAXISMOTION:
            if RuntimeVariables.TrackingTaskPresent:
                # values between -1 and 1. (-1,-1) top left corner, (1,-1) top right; (-1,1) bottom left, (1,1) bottom right
                try:
                    RuntimeVariables.JoystickAxis = Vector2D(RuntimeVariables.JoystickObject.get_axis(0), RuntimeVariables.JoystickObject.get_axis(1))
                except (pygame.error, NameError, AttributeError):
                    # prevent the program crashing when no joystick is connected
                    pass
        elif event.type == pygame.JOYBUTTONUP and not RuntimeVariables.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTyping")
                writeOutputDataFile("ButtonRelease", "-")
        elif event.type == pygame.JOYBUTTONDOWN and not RuntimeVariables.ParallelDualTasks:
            if event.button == 0:  # only respond to 0 button
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")

        elif event.type == pygame.KEYDOWN:
            # F1 key switches windows, alternatively to the joystick button
            if event.key == pygame.K_F1 and RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TypingTaskPresent and not RuntimeVariables.ParallelDualTasks:
                switchWindows("openTyping")
                writeOutputDataFile("ButtonRelease", "-")
            elif event.key == pygame.K_F1 and RuntimeVariables.TypingWindowVisible and RuntimeVariables.TrackingTaskPresent and not RuntimeVariables.ParallelDualTasks:
                switchWindows("openTracking")
                writeOutputDataFile("ButtonPress", "-")
            # F4 key closes the program
            elif event.key == pygame.K_F4:
                quitApp("F4 was typed to terminate the app")
            else:
                # only process keypresses if the digit task is present
                singleTypingTask = RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible
                dualTaskWithSwitching = RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible
                dualTaskParallel = RuntimeVariables.TypingTaskPresent and not RuntimeVariables.TypingWindowVisible and RuntimeVariables.ParallelDualTasks
                if singleTypingTask or dualTaskWithSwitching or dualTaskParallel:
                    key = event.unicode
                    RuntimeVariables.DigitPressTimes.append(time.time())

                    isNeutralKeyPress = False
                    # In parallel dual task, e is to be typed when the cursor was outside the circle. On e, all key presses are neither correct or incorrect.
                    if RuntimeVariables.CurrentTypingTaskNumbers[0] == "e" and RuntimeVariables.ParallelDualTasks and (RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask):
                        isNeutralKeyPress = True
                    # In non-parallel dual tasks, if the cursor is outside the circle and correct inputs don't count outside, treat it as neutral.
                    if not RuntimeVariables.ParallelDualTasks and RuntimeVariables.DisableCorrectTypingScoreOutsideCircle and isCursorOutsideCircle():
                        isNeutralKeyPress = True

                    # Neutral key presses don't count as correct nor incorrect.
                    if isNeutralKeyPress:
                        RuntimeVariables.EnteredDigitsStr += key
                        UpdateTypingTaskString(reset=False)  # generate one new character
                        writeOutputDataFile("keypress", key)
                        print(f"Neutral key press: {key}")
                    # If key press is correct ...
                    elif key == RuntimeVariables.CurrentTypingTaskNumbers[0]:
                        RuntimeVariables.EnteredDigitsStr += key
                        UpdateTypingTaskString(reset=False)  # generate one new character
                        RuntimeVariables.CorrectlyTypedDigitsVisit += 1
                        writeOutputDataFile("keypress", key)
                        print(f"Correct key press: {key}")
                    # If key press is wrong ...
                    else:
                        RuntimeVariables.IncorrectlyTypedDigitsTrial += 1
                        RuntimeVariables.IncorrectlyTypedDigitsVisit += 1
                        writeOutputDataFile("wrongKeypress", key)
                        print(f"Incorrect key press: {key}")

                    if RuntimeVariables.CurrentTask in [TaskTypes.SingleTyping, TaskTypes.PracticeSingleTyping] or not RuntimeVariables.DisplayTypingTaskWithinCursor:
                        drawTypingWindow()


def switchWindows(taskToOpen):
    print("FUNCTION: " + getFunctionName())
    # switching is only done in dual-task
    if RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask:
        if taskToOpen == "openTracking":
            if not RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TrackingTaskPresent:
                openTrackingWindow()
            if RuntimeVariables.TypingWindowVisible and RuntimeVariables.TypingTaskPresent:
                closeTypingWindow()
        elif taskToOpen == "openTyping":
            if not RuntimeVariables.TypingWindowVisible and RuntimeVariables.TypingTaskPresent:
                openTypingWindow()
            if RuntimeVariables.TrackingWindowVisible and RuntimeVariables.TrackingTaskPresent:
                closeTrackingWindow()


def printTextOverMultipleLines(text, location):
    fontsize = ExperimentSettings.GeneralFontSize
    color = (0, 0, 0)
    pygame.event.pump()
    splittedText = text.split("\n")
    lineDistance = (pygame.font.Font(None, fontsize)).get_linesize()
    PositionX = location[0]
    PositionY = location[1]

    for lines in splittedText:
        f = pygame.font.Font(None, fontsize)
        feedbackmessage = f.render(lines, True, color)
        RuntimeVariables.Screen.blit(feedbackmessage, (PositionX, PositionY))
        PositionY = PositionY + lineDistance


def CountdownMessage(displayTime):
    print("FUNCTION: " + getFunctionName())
    for i in range(0, displayTime):
        # prepare background
        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))

        messageAreaObject = pygame.Surface((int(Constants.ExperimentWindowSize.X / 5), int(Constants.ExperimentWindowSize.Y / 5))).convert()
        messageAreaObject.fill((255, 255, 255))

        topCornerOfMessageArea = Vector2D(int(Constants.ExperimentWindowSize.X * 2 / 5), int(Constants.TopLeftCornerOfTypingTaskWindow.Y + 10))
        RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))

        message = "Mach dich bereit!\n\n" \
                  "            " + str(displayTime - i)

        pygame.display.flip()
        printTextOverMultipleLines(message, (topCornerOfMessageArea.X + 45, topCornerOfMessageArea.Y + 10))
        pygame.display.flip()
        time.sleep(1)


def DisplayMessage(message, displayTime):
    print("FUNCTION: " + getFunctionName())
    # prepare background
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))
    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))
    topCornerOfMessageArea = Vector2D(50, 50)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges
    location = Vector2D(topCornerOfMessageArea.X + 75, topCornerOfMessageArea.Y + 75)
    printTextOverMultipleLines(message, (location.X, location.Y))
    pygame.display.flip()
    time.sleep(displayTime)


def drawCanvas():
    print("FUNCTION: " + getFunctionName())
    # prepare background
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))
    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))
    topCornerOfMessageArea = Vector2D(50, 50)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges
    buttonAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 300, Constants.ExperimentWindowSize.Y - 300)).convert()
    buttonAreaObject.fill((150, 150, 150))
    RuntimeVariables.Screen.blit(buttonAreaObject, (150, 150))  # make area 50 pixels away from edges


def reportUserScore():
    print("FUNCTION: " + getFunctionName())
    # prepare background
    completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
    completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
    RuntimeVariables.Screen.blit(completebg, (0, 0))

    messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
    messageAreaObject.fill((255, 255, 255))

    topCornerOfMessageArea = Vector2D(50, 50)
    RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges

    feedbackText = ""
    scoreForLogging = "-"  # score that's logged
    scoresOnThisBlock = []  # stores the scores on the current block. Can be used to report performance each 5th trial

    if RuntimeVariables.CurrentTask == TaskTypes.DualTask:
        feedbackScore = RuntimeVariables.TrialScore
        if RuntimeVariables.TrialScore > 0:
            feedbackText = "+" + str(feedbackScore) + " Punkte"
        else:
            feedbackText = str(feedbackScore) + " Punkte"

        RuntimeVariables.ScoresForPayment.append(RuntimeVariables.TrialScore)
        scoresOnThisBlock.append(RuntimeVariables.TrialScore)  # store score, so average performance can be reported
        scoreForLogging = RuntimeVariables.TrialScore

    elif RuntimeVariables.CurrentTask == TaskTypes.SingleTyping:
        feedbackText = "Anzahl Fehler: \n"
        if RuntimeVariables.TypingTaskPresent:
            digitScore = RuntimeVariables.DigitPressTimes[-1] - RuntimeVariables.DigitPressTimes[0]
            # round values
            digitScore = scipy.special.round(digitScore * 10) / 10
            feedbackText += "\n\n" + str(RuntimeVariables.IncorrectlyTypedDigitsTrial) + " Fehler"
            scoresOnThisBlock.append(RuntimeVariables.IncorrectlyTypedDigitsTrial)
            scoreForLogging = digitScore

    if feedbackText != "":
        location = Vector2D(topCornerOfMessageArea.X + 50, topCornerOfMessageArea.Y + 50)
        printTextOverMultipleLines(feedbackText, (location.X, location.Y))

    pygame.display.flip()
    writeOutputDataFile("scoreGiven", str(scoreForLogging))
    time.sleep(ExperimentSettings.TimeFeedbackIsGiven)

    if len(scoresOnThisBlock) % 5 == 0:  # every fifth trial, report mean score
        # prepare background
        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))
        messageAreaObject = pygame.Surface((Constants.ExperimentWindowSize.X - 100, Constants.ExperimentWindowSize.Y - 100)).convert()
        messageAreaObject.fill((255, 255, 255))
        topCornerOfMessageArea = Vector2D(50, 50)
        RuntimeVariables.Screen.blit(messageAreaObject, (topCornerOfMessageArea.X, topCornerOfMessageArea.Y))  # make area 50 pixels away from edges

        feedbackText2 = "Deine durchschnittliche Punktzahl der letzten 4 Durchgänge:\n\n"
        meanscore = scipy.special.round(scipy.mean(scoresOnThisBlock[-2:]) * 100) / 100  # report meanscore
        feedbackText2 = feedbackText2 + str(meanscore)

        if RuntimeVariables.CurrentTask == TaskTypes.SingleTracking:
            feedbackText2 = feedbackText2 + " pixels"
        elif RuntimeVariables.CurrentTask == TaskTypes.SingleTyping:
            feedbackText2 = feedbackText2 + " errors"
        elif RuntimeVariables.CurrentTask == TaskTypes.DualTask:
            feedbackText2 = "Block " + str(int(len(scoresOnThisBlock) / 3)) + " von 6 vollständig. Deine durchschnittliche Leistung der letzten 4 Durchgänge:\n\n" + str(meanscore) + " points"

        location = Vector2D(topCornerOfMessageArea.X + 50, topCornerOfMessageArea.Y + 50)

        printTextOverMultipleLines(feedbackText2, (location.X, location.Y))
        pygame.display.flip()

        writeOutputDataFile("avscoreGiven", str(meanscore))
        time.sleep(20)


def UpdateTypingTaskString(reset=False):
    """
    Updates the typing task number string.
    :param reset: Set to True if you want to generate a completely new string
    """
    if reset:
        RuntimeVariables.CurrentTypingTaskNumbers = ""
    # Remove the leftmost character
    RuntimeVariables.CurrentTypingTaskNumbers = RuntimeVariables.CurrentTypingTaskNumbers[1:]
    # Generate random characters until the string is complete
    numberOfNewCharacters = RuntimeVariables.CurrentTypingTaskNumbersLength - len(RuntimeVariables.CurrentTypingTaskNumbers)
    if numberOfNewCharacters > 0:
        newCharacters = GetTypingTaskNumbers(numberOfNewCharacters)
        # Update the typing task string. Append the new numbers on the right hand side.
        RuntimeVariables.CurrentTypingTaskNumbers += newCharacters


def GetTypingTaskNumbers(count):
    """
    Returns a random string of characters that are used in the typing task string, depending on the cursor position.
    Returns e if the cursor is outside of the circle.
    :param count: Specifies how many numbers you want
    :return: A string with <count> numbers
    """
    print("FUNCTION: " + getFunctionName())

    # For single typing task or regular dual task with switching, return the single task string
    isSwitchingDualTask = RuntimeVariables.CurrentTask in [TaskTypes.DualTask, TaskTypes.PracticeDualTask] and not RuntimeVariables.ParallelDualTasks
    isSingleTypingTask = RuntimeVariables.CurrentTask in [TaskTypes.SingleTyping, TaskTypes.PracticeSingleTyping]
    if isSwitchingDualTask or isSingleTypingTask:
        return ''.join([random.choice(ExperimentSettings.SingleTypingTaskNumbers) for _ in range(count)])

    # For dual task with both tracking and typing window visible, determine the typing string from the cursor position
    distanceCursorMiddle = math.sqrt((abs(Constants.TrackingWindowMiddleX - RuntimeVariables.CursorCoordinates.X)) ** 2 + (abs(Constants.TrackingWindowMiddleY - RuntimeVariables.CursorCoordinates.Y)) ** 2)
    possibleCharacters = None
    for circle in RuntimeVariables.CurrentCircles:
        if distanceCursorMiddle < circle.Radius:
            possibleCharacters = circle.TypingTaskNumbersDualTask
            break

    # If the cursor is outside the outermost circle radius, the tpying task should show an "e"
    if not possibleCharacters and RuntimeVariables.ParallelDualTasks:
        possibleCharacters = "e"
    elif not possibleCharacters:
        raise Exception("Could not get a random typing task number for the current circle radius!")

    # Return the specified number of random characters
    return ''.join([random.choice(possibleCharacters) for _ in range(count)])


def drawCircles(bg):
    for circle in reversed(RuntimeVariables.CurrentCircles):
        # draw a filled circle
        drawCircle(bg, circle.InnerCircleColor, circle.Radius, 0)
        # Draws a circular shape on the Surface. The pos argument is the center of the circle, and radius is the size.
        #  The width argument is the thickness to draw the outer edge. If width is zero then the circle will be filled.
        drawCircle(bg, circle.BorderColor, circle.Radius, ExperimentSettings.CircleBorderThickness)


def drawCircle(image, colour, radius, width=0):
    origin = Vector2D(int(ExperimentSettings.TaskWindowSize.X / 2), int(ExperimentSettings.TaskWindowSize.Y / 2))
    # based on recommendation on pygame website
    if width == 0:
        pygame.draw.circle(image, colour, (origin.X, origin.Y), int(radius))
    else:
        if radius > 65534 / 5:
            radius = 65534 / 5
        circle = pygame.Surface([radius * 2 + width, radius * 2 + width]).convert_alpha()
        circle.fill([0, 0, 0, 0])
        pygame.draw.circle(circle, colour, (int(circle.get_width() / 2), int(circle.get_height() / 2)), int(radius + (width / 2)))
        if int(radius - (width / 2)) > 0:
            pygame.draw.circle(circle, [0, 0, 0, 0], (int(circle.get_width() / 2), int(circle.get_height() / 2)), abs(int(radius - (width / 2))))
        image.blit(circle, [origin.X - (circle.get_width() / 2), origin.Y - (circle.get_height() / 2)])


def drawCursor(sleepTime):
    restSleepTime = 0
    x = RuntimeVariables.CursorCoordinates.X
    y = RuntimeVariables.CursorCoordinates.Y
    oldX = x
    oldY = y
    final_x = x
    final_y = y

    # only add noise if tracking is not moving
    motionThreshold = 0.08

    joystickAxisWithinThreshold = RuntimeVariables.JoystickAxis.X > motionThreshold or \
                                  RuntimeVariables.JoystickAxis.X < -motionThreshold or \
                                  RuntimeVariables.JoystickAxis.Y > motionThreshold or \
                                  RuntimeVariables.JoystickAxis.Y < -motionThreshold

    if not (RuntimeVariables.TrackingWindowVisible and joystickAxisWithinThreshold):
        final_x = x + random.gauss(0, RuntimeVariables.StandardDeviationOfNoise)
        final_y = y + random.gauss(0, RuntimeVariables.StandardDeviationOfNoise)

    if RuntimeVariables.TrackingWindowVisible:  # only add joystickAxis if the window is open (i.e., if the participant sees what way cursor moves!)
        final_x += RuntimeVariables.JoystickAxis.X * Constants.ScalingJoystickAxis
        final_y += RuntimeVariables.JoystickAxis.Y * Constants.ScalingJoystickAxis

    # now iterate through updates (but only do that if the window is open - if it's closed do it without mini-steps, so as to make computation faster)
    nrUpdates = int(sleepTime / Constants.StepSizeOfTrackingScreenUpdate)
    delta_x = (final_x - x) / nrUpdates
    delta_y = (final_y - y) / nrUpdates

    if RuntimeVariables.TrackingWindowVisible:
        for i in range(0, nrUpdates):
            x += delta_x
            y += delta_y

            if (x, y) != RuntimeVariables.CursorCoordinates:
                # now check if the cursor is still within screen range
                if x < (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2):
                    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2
                elif x > (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2):
                    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2

                if y < (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2):
                    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2
                elif y > (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2):
                    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2

                drawTrackingWindow()
            time.sleep(Constants.StepSizeOfTrackingScreenUpdate)

        # see if there is additional time to sleep
        mods = sleepTime % Constants.StepSizeOfTrackingScreenUpdate
        if mods != 0:
            restSleepTime = mods

    # if tracking window is not visible, just update the values
    else:
        x = final_x
        y = final_y

        # now check if the cursor is still within screen range
        if (x, y) != RuntimeVariables.CursorCoordinates:
            if x < (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2):
                x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.CursorSize.X / 2
            elif x > (Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2):
                x = Constants.TopLeftCornerOfTrackingTaskWindow.X + ExperimentSettings.TaskWindowSize.X - ExperimentSettings.CursorSize.X / 2

            if y < (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2):
                y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.CursorSize.Y / 2
            elif y > (Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2):
                y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y - ExperimentSettings.CursorSize.Y / 2
        # if display is not updated, sleep for entire time
        restSleepTime = sleepTime

    # always update coordinates
    RuntimeVariables.CursorCoordinates = Vector2D(x, y)

    # collect distances of the cursor to the circle middle for the RMSE
    RuntimeVariables.CursorDistancesToMiddle.append(math.sqrt((Constants.TrackingWindowMiddleX - x) ** 2 + (Constants.TrackingWindowMiddleY - y) ** 2))

    # collect cumulatively the distance the cursor has moved
    RuntimeVariables.LengthOfPathTracked += math.sqrt((oldX - x) ** 2 + (oldY - y) ** 2)

    # Detect whether the cursor is outside the circle, also if tracking is not visible.
    if isCursorOutsideCircle():
        RuntimeVariables.CurrentCursorColor = ExperimentSettings.CursorColorInside
    else:
        RuntimeVariables.CurrentCursorColor = ExperimentSettings.CursorColorOutside

    # For Parallel DualTasks, update the typing task string on cursor leaving/reentering the circle
    if RuntimeVariables.ParallelDualTasks and RuntimeVariables.TrackingWindowVisible:
        # When the cursor moves outside the circles, the parallel dual task typing number shall become "e" immediately
        if isCursorOutsideCircle() and not RuntimeVariables.WasCursorOutsideRadiusBefore:
            RuntimeVariables.CurrentTypingTaskNumbers = "e"
        # When the cursor moves back inside the circles, the parallel dual task typing number shall become a number immediately
        if not isCursorOutsideCircle() and RuntimeVariables.WasCursorOutsideRadiusBefore and RuntimeVariables.CurrentTask not in [TaskTypes.SingleTracking, TaskTypes.PracticeSingleTracking]:
            UpdateTypingTaskString(reset=False)

    RuntimeVariables.WasCursorOutsideRadiusBefore = isCursorOutsideCircle()
    return restSleepTime


def isCursorOutsideCircle():
    try:
        position = RuntimeVariables.CursorCoordinates
        distanceCursorMiddle = math.sqrt((abs(Constants.TrackingWindowMiddleX - position.X)) ** 2 + (abs(Constants.TrackingWindowMiddleY - position.Y)) ** 2)
        largestCircleRadius = max(list(map(lambda circle: circle.Radius, RuntimeVariables.CurrentCircles)))
        return distanceCursorMiddle > largestCircleRadius
    except:
        return False


def drawTypingTaskWithinCursor():
    fontsize = ExperimentSettings.FontSizeTypingTaskNumberWithinCursor
    f = pygame.font.Font(None, fontsize)
    typingTaskNumberText = f.render(RuntimeVariables.CurrentTypingTaskNumbers, True, ExperimentSettings.FontColorTypingTaskNumberWithinCursor)
    textWidth, textHeight = f.size(RuntimeVariables.CurrentTypingTaskNumbers)
    x = RuntimeVariables.CursorCoordinates.X - (textWidth / 2)
    y = RuntimeVariables.CursorCoordinates.Y - (textHeight / 2)
    RuntimeVariables.Screen.blit(typingTaskNumberText, (x, y))


def closeTypingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.TypingWindowVisible = False
    RuntimeVariables.VisitEndTime = time.time()


def drawCover(windowSide):
    if windowSide == "typing":
        location = Constants.TopLeftCornerOfTypingTaskWindow
    elif windowSide == "tracking":
        location = Constants.TopLeftCornerOfTrackingTaskWindow
    else:
        raise Exception("invalid window side specified")

    # draw background
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.CoverColor)
    RuntimeVariables.Screen.blit(bg, (location.X, location.Y))  # make area about 30 away from centre


def openTypingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.VisitStartTime = time.time()
    RuntimeVariables.CorrectlyTypedDigitsVisit = 0
    RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
    RuntimeVariables.TypingWindowEntryCounter = RuntimeVariables.TypingWindowEntryCounter + 1
    drawTypingWindow()
    RuntimeVariables.TypingWindowVisible = True


def drawTypingWindow():
    # draw background
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
    RuntimeVariables.Screen.blit(bg, (Constants.TopLeftCornerOfTypingTaskWindow.X, Constants.TopLeftCornerOfTypingTaskWindow.Y))  # make area about 30 away from centre

    if not RuntimeVariables.ParallelDualTasks and (RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask):
        drawCover("tracking")

    fontsize = ExperimentSettings.FontSizeTypingTaskNumberSingleTask
    f = pygame.font.Font(None, fontsize)
    typingTaskNumberText = f.render(RuntimeVariables.CurrentTypingTaskNumbers, True, (0, 0, 0))
    textWidth, textHeight = f.size(RuntimeVariables.CurrentTypingTaskNumbers)
    x = (Constants.TopLeftCornerOfTypingTaskWindow.X + ExperimentSettings.TaskWindowSize.X / 2) - (textWidth / 2)
    y = (Constants.TopLeftCornerOfTypingTaskWindow.Y + ExperimentSettings.TaskWindowSize.Y / 2) - (textHeight / 2)
    RuntimeVariables.Screen.blit(typingTaskNumberText, (x, y))


def closeTrackingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.TrackingWindowVisible = False
    RuntimeVariables.VisitEndTime = time.time()


def openTrackingWindow():
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.VisitStartTime = time.time()
    RuntimeVariables.TrackingWindowEntryCounter += 1

    if RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask:
        ApplyRewardForTypingTaskScores()

    RuntimeVariables.TrackingWindowVisible = True

    # get the cursor angle
    # prevent the program crashing when no joystick is connected
    try:
        RuntimeVariables.JoystickAxis = Vector2D(RuntimeVariables.JoystickObject.get_axis(0), RuntimeVariables.JoystickObject.get_axis(1))
    except (pygame.error, NameError, AttributeError):
        pass


def drawTrackingWindow():
    # draw background
    bg = pygame.Surface((ExperimentSettings.TaskWindowSize.X, ExperimentSettings.TaskWindowSize.Y)).convert()
    bg.fill(ExperimentSettings.BackgroundColorTaskWindows)
    drawCircles(bg)
    RuntimeVariables.Screen.blit(bg, (Constants.TopLeftCornerOfTrackingTaskWindow.X, Constants.TopLeftCornerOfTrackingTaskWindow.Y))  # make area about 30 away from centre
    newCursorLocation = Vector2D(RuntimeVariables.CursorCoordinates.X - (ExperimentSettings.CursorSize.X / 2), RuntimeVariables.CursorCoordinates.Y - (ExperimentSettings.CursorSize.Y / 2))
    newCursor = pygame.Surface((ExperimentSettings.CursorSize.X, ExperimentSettings.CursorSize.Y)).convert()
    newCursor.fill(RuntimeVariables.CurrentCursorColor)
    RuntimeVariables.Screen.blit(newCursor, (newCursorLocation.X, newCursorLocation.Y))  # blit puts something new on the screen

    # Show the number of points above the tracking circle
    if RuntimeVariables.Penalty != "none" and (RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask) and not RuntimeVariables.ParallelDualTasks:
        drawDualTaskScore()


def drawDualTaskScore():
    intermediateMessage = str(RuntimeVariables.VisitScore) + " Punkte"
    fontsize = ExperimentSettings.GeneralFontSize
    f = pygame.font.Font(None, fontsize)
    textWidth, textHeight = f.size(intermediateMessage)
    x = Constants.TopLeftCornerOfTrackingTaskWindow.X + (ExperimentSettings.TaskWindowSize.X / 2) - (textWidth / 2)
    y = Constants.TopLeftCornerOfTrackingTaskWindow.Y + 10
    printTextOverMultipleLines(intermediateMessage, (x, y))


def ApplyRewardForTypingTaskScores():
    """
    For dual tasks: Calculates a reward for the user score. If the cursor is outside of the circle, the possible reward is reduced.
    This function is called at the end of a dual task trial or when switching from tracking to typing window.
    """
    print("FUNCTION: " + getFunctionName())
    # This is the typing reward and the typing penalty
    gainFormula = (RuntimeVariables.CorrectlyTypedDigitsVisit * RuntimeVariables.GainCorrectDigit) - (RuntimeVariables.IncorrectlyTypedDigitsVisit * RuntimeVariables.GainIncorrectDigit)

    # If Cursor is inside the circle, apply the full reward
    if not isCursorOutsideCircle() or RuntimeVariables.Penalty == Penalty.NoPenalty:
        RuntimeVariables.VisitScore = gainFormula
    # If Cursor is outside of the circle, reduce the reward (tracking penalty)
    else:
        RuntimeVariables.NumberOfCircleExits += 1
        if RuntimeVariables.Penalty == Penalty.LoseAmount:
            # reduce the reward by an amount, e.g. 500 ("lose500")
            RuntimeVariables.VisitScore = gainFormula - RuntimeVariables.PenaltyAmount
        elif RuntimeVariables.Penalty == Penalty.LoseAll:
            # lose all points by setting the score to 0
            RuntimeVariables.VisitScore = 0
        elif RuntimeVariables.Penalty == Penalty.LoseHalf:
            # reduce the reward by the half
            RuntimeVariables.VisitScore = 0.5 * gainFormula

    # add the score for this digit task visit to the overall trial score
    # trial score is used in reportUserScore
    RuntimeVariables.TrialScore += RuntimeVariables.VisitScore
    writeOutputDataFile("updatedVisitScore", str(RuntimeVariables.VisitScore))


def runSingleTaskTypingTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTask = TaskTypes.PracticeSingleTyping
        DisplayMessage("Nur Tippen\n\n"
                       "In diesen Durchgängen übst du nur die Tippaufgabe.\n"
                       "Kopiere die Ziffern, die dir auf dem Bildschirm angezeigt werden so schnell wie möglich.\n\n"
                       "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n"
                       "(In zukünftigen Durchgängen würdest du dadurch Punkte verlieren.)", 15)
    else:
        RuntimeVariables.CurrentTask = TaskTypes.SingleTyping
        DisplayMessage("Nur Tippen\n\n"
                       "Kopiere die Ziffern so schnell wie möglich.\n"
                       "Wenn du einen Fehler machst, wird die Ziffernfolge nicht fortgesetzt.\n", 10)

    RuntimeVariables.CurrentTypingTaskNumbersLength = ExperimentSettings.SingleTypingTaskNumbersLength

    for i in range(0, numberOfTrials):
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0

        CountdownMessage(3)
        pygame.event.clear()  # clear all events
        RuntimeVariables.TrackingWindowVisible = False
        RuntimeVariables.TypingWindowVisible = True

        RuntimeVariables.TrackingTaskPresent = False
        RuntimeVariables.TypingTaskPresent = True
        RuntimeVariables.TrialNumber += 1
        RuntimeVariables.TrackingWindowEntryCounter = 0
        RuntimeVariables.TypingWindowEntryCounter = 0

        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))

        RuntimeVariables.StartTimeCurrentTrial = time.time()

        if RuntimeVariables.TypingTaskPresent:
            UpdateTypingTaskString(reset=True)  # generate numbers initially
            RuntimeVariables.EnteredDigitsStr = ""
            RuntimeVariables.DigitPressTimes = [RuntimeVariables.StartTimeCurrentTrial]

            if RuntimeVariables.TypingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeOutputDataFile("trialStart", "-")

        while (time.time() - RuntimeVariables.StartTimeCurrentTrial) < ExperimentSettings.MaxTrialTimeSingleTyping and RuntimeVariables.EnvironmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates
            pygame.display.flip()
            time.sleep(0.02)

        if (time.time() - RuntimeVariables.StartTimeCurrentTrial) >= ExperimentSettings.MaxTrialTimeSingleTyping:
            writeOutputDataFile("trialStopTooMuchTime", "-", True)
        elif not RuntimeVariables.EnvironmentIsRunning:
            writeOutputDataFile("trialStopEnvironmentStopped", "-", True)
        else:
            writeOutputDataFile("trialStop", "-", True)

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def runSingleTaskTrackingTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTask = TaskTypes.PracticeSingleTracking
        DisplayMessage(
            "Nur Tracking\n\n"
            "In diesen Durchgängen übst du nur die Trackingaufgabe.\n"
            "Du kannst ausprobieren, wie der Joystick funktioniert und sehen, wie schnell der blaue Cursor umherwandert.\n"
            "Der Cursor bewegt sich so lange frei herum, bis du ihn mit dem Joystick bewegst.\n"
            "Denk daran: deine Aufgabe ist es, zu verhindern, dass der blaue Cursor den Kreis verlässt!",
            15)
    else:
        RuntimeVariables.CurrentTask = TaskTypes.SingleTracking
        DisplayMessage(
            "Nur Tracking\n\n"
            "Nutze diesen Durchgang, um dich mit der Geschwindigkeit des Cursors vertraut zu machen, \n"
            "und denk daran den Cursor mit deinem Joystick in der Kreismitte zu halten.",
            10)

    for i in range(0, numberOfTrials):
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        CountdownMessage(3)
        pygame.event.clear()
        RuntimeVariables.TrackingWindowVisible = True
        RuntimeVariables.TypingWindowVisible = False
        RuntimeVariables.TrackingTaskPresent = True
        RuntimeVariables.TypingTaskPresent = False
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0

        RuntimeVariables.TrialNumber = RuntimeVariables.TrialNumber + 1
        bg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        bg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(bg, (0, 0))

        RuntimeVariables.StartTimeCurrentTrial = time.time()

        RuntimeVariables.TrackingWindowEntryCounter = 0
        RuntimeVariables.TypingWindowEntryCounter = 0
        RuntimeVariables.CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)

        if RuntimeVariables.TrackingTaskPresent:
            RuntimeVariables.JoystickAxis = Vector2D(0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                RuntimeVariables.JoystickObject = pygame.joystick.Joystick(0)
                RuntimeVariables.JoystickObject.init()
            except (pygame.error, NameError):
                pass

            if RuntimeVariables.TrackingWindowVisible:
                openTrackingWindow()
            else:
                closeTrackingWindow()

        writeOutputDataFile("trialStart", "-")

        while ((time.time() - RuntimeVariables.StartTimeCurrentTrial) < ExperimentSettings.MaxTrialTimeSingleTracking) and RuntimeVariables.EnvironmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the trackingtask and the typingTask and starts relevant display updates

            restSleepTime = 0
            if RuntimeVariables.TrackingTaskPresent and RuntimeVariables.TrackingWindowVisible:
                drawTrackingWindow()
                restSleepTime = drawCursor(0.02)
                writeOutputDataFile("trackingVisible", "-")

            pygame.display.flip()
            time.sleep(restSleepTime)

        if not RuntimeVariables.EnvironmentIsRunning:
            writeOutputDataFile("trialEnvironmentRunning", "-", True)
        else:
            writeOutputDataFile("trialEnvironmentStopped", "-", True)


def runDualTaskTrials(isPracticeTrial, numberOfTrials):
    print("FUNCTION: " + getFunctionName())
    RuntimeVariables.BlockNumber += 1

    if isPracticeTrial:
        RuntimeVariables.CurrentTask = TaskTypes.PracticeDualTask
        message = "Tracking + Tippen (MULTITASKING)\n\n" \
                  "Du übst jetzt beide Aufgaben gleichzeitig!\n\n"
        if not RuntimeVariables.ParallelDualTasks:
            message += "Die Ziffernaufgabe wird dir immer zuerst angezeigt.\n" \
                       "Drücke den Schalter unter deinem Zeigefinger am Joystick, um zu kontrollieren ob der blaue Cursor\n" \
                       "noch innerhalb des Kreises ist.\n" \
                       "Lasse den Schalter wieder los, um zur Ziffernaufgabe zurück zu gelangen.\n" \
                       "Du kannst immer nur eine Aufgabe bearbeiten."
        DisplayMessage(message, 10)
        message = "Dein Ziel:\n\n" \
                  "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte.\n" \
                  "Fehler beim Tippen führen zu Punkteverlust.\n"
        if not RuntimeVariables.Penalty == Penalty.NoPenalty:
            message += "Aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
        DisplayMessage(message, 10)


    # Normal (no practice) trial
    else:
        RuntimeVariables.CurrentTask = TaskTypes.DualTask
        message = "Dein Ziel:\n\n" \
                  "Kopiere die Ziffern so schnell wie möglich, dadurch gewinnst du Punkte.\n" \
                  "Fehler beim Tippen führen zu Punkteverlust.\n"
        if not RuntimeVariables.Penalty == Penalty.NoPenalty:
            message += "Aber pass auf, dass der Cursor den Kreis nicht verlässt, sonst verlierst du Punkte.\n"
        message += "Wichtig: Deine Leistung in diesen Durchgängen zählt für deine Gesamtpunktzahl."
        DisplayMessage(message, 18)
        if not RuntimeVariables.ParallelDualTasks:
            DisplayMessage("Drücke den Schalter unter deinem Zeigefinger, um das Trackingfenster zu öffnen.\n"
                           "Um wieder zurück zur Tippaufgabe zu gelangen, lässt du den Schalter wieder los.\n"
                           "Du kannst immer nur eine Aufgabe bearbeiten.", 15)

    RuntimeVariables.CurrentTypingTaskNumbersLength = 1 if RuntimeVariables.ParallelDualTasks else ExperimentSettings.SingleTypingTaskNumbersLength

    for i in range(0, numberOfTrials):
        RuntimeVariables.NumberOfCircleExits = 0
        RuntimeVariables.TrialScore = 0
        RuntimeVariables.CorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsVisit = 0
        RuntimeVariables.IncorrectlyTypedDigitsTrial = 0
        RuntimeVariables.CursorDistancesToMiddle = []
        RuntimeVariables.LengthOfPathTracked = 0

        CountdownMessage(3)
        pygame.event.clear()  # clear all events

        if RuntimeVariables.DisplayTypingTaskWithinCursor:
            RuntimeVariables.TrackingWindowVisible = True
            RuntimeVariables.TypingWindowVisible = False
        elif RuntimeVariables.ParallelDualTasks:
            RuntimeVariables.TrackingWindowVisible = True
            RuntimeVariables.TypingWindowVisible = True
        else:  # normal dual task with switching
            RuntimeVariables.TrackingWindowVisible = False
            RuntimeVariables.TypingWindowVisible = True

        RuntimeVariables.TrackingTaskPresent = True
        RuntimeVariables.TypingTaskPresent = True

        RuntimeVariables.TrackingWindowEntryCounter = 0
        RuntimeVariables.TypingWindowEntryCounter = 0
        RuntimeVariables.TrialNumber = RuntimeVariables.TrialNumber + 1
        RuntimeVariables.CursorCoordinates = Vector2D(Constants.TrackingWindowMiddleX, Constants.TrackingWindowMiddleY)

        completebg = pygame.Surface((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y)).convert()
        completebg.fill(ExperimentSettings.BackgroundColorEntireScreen)
        RuntimeVariables.Screen.blit(completebg, (0, 0))

        RuntimeVariables.StartTimeCurrentTrial = time.time()

        if RuntimeVariables.TrackingTaskPresent:
            RuntimeVariables.JoystickAxis = Vector2D(0, 0)
            # prevent the program crashing when no joystick is connected
            try:
                pygame.joystick.init()
                RuntimeVariables.JoystickObject = pygame.joystick.Joystick(0)
                RuntimeVariables.JoystickObject.init()
            except (pygame.error, NameError):
                pass

            if RuntimeVariables.TrackingWindowVisible:
                openTrackingWindow()
            else:
                closeTrackingWindow()

        if RuntimeVariables.TypingTaskPresent:
            UpdateTypingTaskString(reset=True)  # generate numbers initially
            RuntimeVariables.EnteredDigitsStr = ""
            RuntimeVariables.DigitPressTimes = [RuntimeVariables.StartTimeCurrentTrial]
            if RuntimeVariables.TypingWindowVisible:
                openTypingWindow()
            else:
                closeTypingWindow()

        writeOutputDataFile("trialStart", "-")

        while (time.time() - RuntimeVariables.StartTimeCurrentTrial) < ExperimentSettings.MaxTrialTimeDual and RuntimeVariables.EnvironmentIsRunning:
            checkKeyPressed()  # checks keypresses for both the tracking task and the typingTask and starts relevant display updates
            restSleepTime = drawCursor(0.02)  # also draws tracking window
            if RuntimeVariables.TrackingTaskPresent and RuntimeVariables.TrackingWindowVisible:
                if not RuntimeVariables.ParallelDualTasks:
                    drawCover("typing")
                if RuntimeVariables.DisplayTypingTaskWithinCursor and RuntimeVariables.ParallelDualTasks:
                    drawTypingTaskWithinCursor()
            if RuntimeVariables.ParallelDualTasks and RuntimeVariables.TypingTaskPresent and RuntimeVariables.TypingWindowVisible and not RuntimeVariables.DisplayTypingTaskWithinCursor:
                drawTypingWindow()

            pygame.display.flip()
            time.sleep(restSleepTime)

            if RuntimeVariables.ParallelDualTasks:
                eventMsg = "trackingAndTypingVisible"
            elif RuntimeVariables.TrackingWindowVisible:
                eventMsg = "trackingVisible"
            elif RuntimeVariables.TypingWindowVisible:
                eventMsg = "typingVisible"
            else:
                eventMsg = ""

            writeOutputDataFile(eventMsg, "-")

        RuntimeVariables.VisitEndTime = time.time()
        ApplyRewardForTypingTaskScores()

        if (time.time() - RuntimeVariables.StartTimeCurrentTrial) >= ExperimentSettings.MaxTrialTimeDual:
            writeOutputDataFile("trialStopTooMuchTime", "-", True)
        elif not RuntimeVariables.EnvironmentIsRunning:
            writeOutputDataFile("trialStopEnvironmentStopped", "-", True)
        else:
            writeOutputDataFile("trialStop", "-", True)

        if not isPracticeTrial:
            # now give feedback
            reportUserScore()


def ShowStartExperimentScreen():
    drawCanvas()
    location = Vector2D(175, 175)

    message = "Experimentalleiter bitte hier drücken."
    printTextOverMultipleLines(message, (location.X, location.Y))
    pygame.display.flip()

    while not checkMouseClicked():  # wait for a mouseclick
        time.sleep(0.25)
    RuntimeVariables.StartTimeCurrentTrial = time.time()


def StartExperiment():
    # Sort the circle lists by radius to make getting the typing task numbers work properly
    RuntimeVariables.CirclesSmall.sort(key=lambda circle: circle.Radius, reverse=False)
    RuntimeVariables.CirclesBig.sort(key=lambda circle: circle.Radius, reverse=False)
    RuntimeVariables.CirclesPractice.sort(key=lambda circle: circle.Radius, reverse=False)

    conditions = readParticipantFile()
    initializeOutputFiles()
    RuntimeVariables.StartTimeOfFirstExperiment = time.time()

    pygame.init()
    if ExperimentSettings.Fullscreen:
        RuntimeVariables.Screen = pygame.display.set_mode((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y), pygame.FULLSCREEN)
    else:
        RuntimeVariables.Screen = pygame.display.set_mode((Constants.ExperimentWindowSize.X, Constants.ExperimentWindowSize.Y))
    pygame.display.set_caption(Constants.Title)

    # verify all conditions before the experiment starts so that the program would crash at the start if it does
    conditionsVerified = []
    for currentCondition in conditions:
        conditionStandardDeviationOfNoise = currentCondition['standardDeviationOfNoise']
        conditionCircleSize = currentCondition['circleSize']
        conditionPenalty = currentCondition['penalty']
        conditionGainCorrectDigit = currentCondition['gainCorrectDigit']

        # noise values are h (high), m (medium) or l (low)
        if conditionStandardDeviationOfNoise == "high":
            standardDeviationOfNoise = ExperimentSettings.CursorNoises["high"]
            noiseMsg = "hoher"
        elif conditionStandardDeviationOfNoise == "medium":
            standardDeviationOfNoise = ExperimentSettings.CursorNoises["medium"]
            noiseMsg = "mittlerer"
        elif conditionStandardDeviationOfNoise == "low":
            standardDeviationOfNoise = ExperimentSettings.CursorNoises["low"]
            noiseMsg = "niedriger"
        else:
            raise Exception("Invalid noise: " + conditionStandardDeviationOfNoise)

        # radius is small or big
        if conditionCircleSize == "small":  # small radius
            radiusCircle = RuntimeVariables.CirclesSmall
        elif conditionCircleSize == "big":
            radiusCircle = RuntimeVariables.CirclesBig
        else:
            raise Exception("Invalid circle size: " + conditionCircleSize)

        # only if the fourth digit is specified, define penalty
        penaltyAmount = 0
        if conditionPenalty == "all":
            penalty = Penalty.LoseAll
            penaltyMsg = "alle"
        elif conditionPenalty == "half":
            penalty = Penalty.LoseHalf
            penaltyMsg = "die Hälfte deiner"
        elif conditionPenalty == "none":  # No penalty (don't change score on leaving circle)
            penalty = Penalty.NoPenalty
            penaltyMsg = "-"  # won't be shown in this case
        else:  # else penalty must be a number, e.g. 500 for lose500
            try:
                penaltyAmount = int(conditionPenalty)
                penalty = Penalty.LoseAmount
                penaltyMsg = str(penaltyAmount)
            except:
                raise Exception("Invalid penalty: " + conditionPenalty)

        # Verifying all conditions before the first condition starts avoids errors in the middle of the trials
        conditionsVerified.append({
            "standardDeviationOfNoise": standardDeviationOfNoise,
            "noiseMsg": noiseMsg,
            "radiusCircle": radiusCircle,
            "penalty": penalty,
            "penaltyMsg": penaltyMsg,
            "penaltyAmount": penaltyAmount,
            "conditionGainCorrectDigit": conditionGainCorrectDigit
        })

    ShowStartExperimentScreen()
    RuntimeVariables.StartTime = time.time()

    if RuntimeVariables.RunPracticeTrials:
        DisplayMessage("Willkommen zum Experiment!\n\n\n"
                       "Wir beginnen mit den Übungsdurchläufen.", 10)

        # do practice trials
        RuntimeVariables.CurrentCircles = RuntimeVariables.CirclesPractice
        RuntimeVariables.Penalty = ExperimentSettings.PenaltyPracticeTrials
        RuntimeVariables.StandardDeviationOfNoise = ExperimentSettings.CursorNoisePracticeTrials
        for block in RuntimeVariables.RunningOrder:
            if block.TaskType == TaskTypes.PracticeSingleTracking:
                runSingleTaskTrackingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeSingleTyping:
                runSingleTaskTypingTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)
            elif block.TaskType == TaskTypes.PracticeDualTask:
                runDualTaskTrials(isPracticeTrial=True, numberOfTrials=block.NumberOfTrials)

        DisplayMessage("Nun beginnt der Hauppteil und wir testen deine Leistung in den Aufgaben, die du \n"
                       "gerade geübt hast.\n"
                       "Versuche im Laufe des Experiments so viele Punkte wie möglich zu gewinnen!", 10)

    # main experiment loop with verified conditions
    for condition in conditionsVerified:
        # set global and local variables
        RuntimeVariables.StandardDeviationOfNoise = condition["standardDeviationOfNoise"]
        noiseMsg = condition["noiseMsg"]
        RuntimeVariables.CurrentCircles = condition["radiusCircle"]
        RuntimeVariables.Penalty = condition["penalty"]
        RuntimeVariables.PenaltyAmount = condition["penaltyAmount"]
        penaltyMsg = condition["penaltyMsg"]
        RuntimeVariables.GainCorrectDigit = condition["conditionGainCorrectDigit"]

        for block in RuntimeVariables.RunningOrder:
            if block.TaskType == TaskTypes.SingleTracking:
                message = getMessageBeforeTrial(TaskTypes.SingleTracking, noiseMsg, penaltyMsg)
                DisplayMessage(message, 12)
                runSingleTaskTrackingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.SingleTyping:
                message = getMessageBeforeTrial(TaskTypes.SingleTyping, noiseMsg, penaltyMsg)
                DisplayMessage(message, 12)
                runSingleTaskTypingTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)
            if block.TaskType == TaskTypes.DualTask:
                message = getMessageBeforeTrial(TaskTypes.DualTask, noiseMsg, penaltyMsg)
                DisplayMessage(message, 12)
                runDualTaskTrials(isPracticeTrial=False, numberOfTrials=block.NumberOfTrials)

        message = "Bisher hast du: " + str(scipy.sum(RuntimeVariables.ScoresForPayment)) + " Punkte"
        DisplayMessage(message, 8)

    DisplayMessage("Dies ist das Ende der Studie.", 10)
    quitApp()


def getMessageBeforeTrial(trialType, noiseMsg, penaltyMsg):
    message = "NEUER BLOCK: \n\n\n"
    if trialType == TaskTypes.SingleTracking or trialType == TaskTypes.DualTask:
        message += "In den folgenden Durchgängen bewegt sich der Cursor mit " + noiseMsg + " Geschwindigkeit. \n"
    if trialType == TaskTypes.SingleTyping or trialType == TaskTypes.DualTask:
        message += "Für jede korrekt eingegebene Ziffer bekommst du 10 Punkte. \n"
    if RuntimeVariables.ShowPenaltyRewardNoise:
        if trialType == TaskTypes.SingleTyping or trialType == TaskTypes.DualTask:
            message += "Bei jeder falsch eingetippten Ziffer verlierst du 5 Punkte. \n"
        if (trialType == TaskTypes.SingleTracking or trialType == TaskTypes.DualTask) and RuntimeVariables.Penalty != Penalty.NoPenalty:
            message += "Achtung: Wenn der Cursor den Kreis verlässt, verlierst du " + penaltyMsg + " deiner Punkte."
    elif RuntimeVariables.ShowPenaltyRewardNoise:
        if trialType == TaskTypes.DualTask and RuntimeVariables.Penalty != Penalty.NoPenalty:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern und wenn der Punkt den Kreis verlässt."
        if trialType == TaskTypes.DualTask:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern."
        elif trialType == TaskTypes.SingleTracking and RuntimeVariables.Penalty != Penalty.NoPenalty:
            message += "Achtung: Du verlierst Punkte wenn der Punkt den Kreis verlässt."
        elif trialType == TaskTypes.SingleTyping:
            message += "Achtung: Du verlierst Punkte für falsch eingegebene Ziffern."
    return message


def readCsvFile(filePath):
    """
    Reads a multi-line CSV file separated with ;
    """
    f = open(filePath, 'r')
    individualLines = f.read().split('\n')
    f.close()
    lines = list(map(lambda x: x.split(';'), individualLines))  # split all elements
    return [i for i in lines if [j for j in i if j != '']]  # filter out empty lines


def readParticipantFile():
    """
    Loads the conditions from the participant csv file.
    :returns A list of dictionaries
    """
    filename = f'participant_{RuntimeVariables.ParticipantNumber}.csv'
    try:
        lines = readCsvFile(filename)
    except:
        raise Exception(f"Could not read {filename}")
    conditions = []
    for line in lines:
        try:
            if line[0] == "StandardDeviationOfNoise":  # skip column title line
                continue
            conditions.append({
                'standardDeviationOfNoise': line[0],
                'circleSize': line[1],
                'penalty': line[2],
                'gainCorrectDigit': int(line[3])
            })
        except:
            raise Exception(f"Error in {filename} with line: {line}")
    return conditions


def initializeOutputFiles():
    """
    Set the participant condition. Initialize the output files
    """
    outputText = \
        "SubjectNr" + ";" \
        "RadiusCircle" + ";" \
        "StandardDeviationOfNoise" + ";" \
        "CurrentTime" + ";" \
        "TrialTime" + ";" \
        "VisitTime" + ";" \
        "BlockNumber" + ";" \
        "TrialNumber" + ";" \
        "Experiment" + ";" \
        "TrackingTaskPresent" + ";" \
        "TypingTaskPresent" + ";" \
        "TrackingWindowVisible" + ";" \
        "TypingWindowVisible" + ";" \
        "TrackingWindowEntryCounter" + ";" \
        "TypingWindowEntryCounter" + ";" \
        "RMSE" + ";" \
        "LengthPathTrackedPixel" + ";" \
        "CursorCoordinatesX" + ";" \
        "CursorCoordinatesY" + ";" \
        "JoystickAxisX" + ";" \
        "JoystickAxisY" + ";" \
        "EnteredDigits" + ";" \
        "EnteredDigitsLength" + ";" \
        "RuntimeExperimentVariables.CurrentTypingTaskNumbers" + ";" \
        "GeneratedTypingTaskNumberLength" + ";" \
        "NumberOfCircleExits" + ";" \
        "TrialScore" + ";" \
        "VisitScore" + ";" \
        "CorrectDigitsVisit" + ";" \
        "IncorrectDigitsVisit" + ";" \
        "IncorrectDigitsTrial" + ";" \
        "OutsideRadius" + ";" \
        "GainCorrectDigit" + ";" \
        "EventMessage1" + ";" \
        "EventMessage2" + "\n"

    timestamp = time.strftime("%Y-%m-%d_%H-%M")
    dataFileName = "participant_" + str(RuntimeVariables.ParticipantNumber) + "_data_" + timestamp + ".csv"
    RuntimeVariables.OutputDataFile = open(dataFileName, 'w')  # contains the user data
    RuntimeVariables.OutputDataFile.write(outputText)
    RuntimeVariables.OutputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFile.fileno())

    summaryFileName = "participant_" + str(RuntimeVariables.ParticipantNumber) + "_data_lastTrialEntry_" + timestamp + ".csv"
    RuntimeVariables.OutputDataFileTrialEnd = open(summaryFileName, 'w')  # contains the user data
    RuntimeVariables.OutputDataFileTrialEnd.write(outputText)
    RuntimeVariables.OutputDataFileTrialEnd.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFileTrialEnd.fileno())


def writeOutputDataFile(eventMessage1, eventMessage2, endOfTrial=False):
    currentTime = time.time() - RuntimeVariables.StartTimeOfFirstExperiment  # this is an absolute time, that always increases (necessary to syncronize with eye-tracking)
    currentTime = scipy.special.round(currentTime * 10000) / 10000

    trialTime = time.time() - RuntimeVariables.StartTimeCurrentTrial  # this is a local time (reset at the start of each trial) in seconds
    trialTime = scipy.special.round(trialTime * 10000) / 10000

    if not RuntimeVariables.TrackingTaskPresent:
        outputCursorCoordinateX = "-"
        outputCursorCoordinateY = "-"
        outputJoystickAxisX = "-"
        outputJoystickAxisY = "-"
    else:
        outputCursorCoordinateX = scipy.special.round(RuntimeVariables.CursorCoordinates.X * 100) / 100
        outputCursorCoordinateY = scipy.special.round(RuntimeVariables.CursorCoordinates.Y * 100) / 100
        outputJoystickAxisX = scipy.special.round(RuntimeVariables.JoystickAxis.X * 1000) / 1000
        outputJoystickAxisY = scipy.special.round(RuntimeVariables.JoystickAxis.Y * 1000) / 1000

    if RuntimeVariables.TypingTaskPresent:
        outputEnteredDigitsStr = RuntimeVariables.EnteredDigitsStr
        outputEnteredDigitsLength = len(RuntimeVariables.EnteredDigitsStr)
        outputGeneratedTypingTaskNumbers = RuntimeVariables.CurrentTypingTaskNumbers
        outputGeneratedTypingTaskNumbersLength = len(RuntimeVariables.CurrentTypingTaskNumbers)
    else:
        outputEnteredDigitsStr = "-"
        outputEnteredDigitsLength = "-"
        outputGeneratedTypingTaskNumbers = "-"
        outputGeneratedTypingTaskNumbersLength = "-"

    if RuntimeVariables.CurrentTask == TaskTypes.DualTask or RuntimeVariables.CurrentTask == TaskTypes.PracticeDualTask:
        visitTime = time.time() - RuntimeVariables.VisitStartTime
    else:
        visitTime = "-"

    circleRadii = list(map(lambda circle: circle.Radius, RuntimeVariables.CurrentCircles))
    currentTask = str(RuntimeVariables.CurrentTask)

    outputText = \
        str(RuntimeVariables.ParticipantNumber) + ";" + \
        str(circleRadii) + ";" + \
        str(RuntimeVariables.StandardDeviationOfNoise) + ";" + \
        str(currentTime) + ";" + \
        str(trialTime) + ";" + \
        str(visitTime) + ";" + \
        str(RuntimeVariables.BlockNumber) + ";" + \
        str(RuntimeVariables.TrialNumber) + ";" + \
        str(currentTask) + ";" + \
        str(RuntimeVariables.TrackingTaskPresent) + ";" + \
        str(RuntimeVariables.TypingTaskPresent) + ";" + \
        str(RuntimeVariables.TrackingWindowVisible) + ";" + \
        str(RuntimeVariables.TypingWindowVisible) + ";" + \
        str(RuntimeVariables.TrackingWindowEntryCounter) + ";" + \
        str(RuntimeVariables.TypingWindowEntryCounter) + ";" + \
        str(calculateRmse(clearDistances=endOfTrial)) + ";" + \
        str(RuntimeVariables.LengthOfPathTracked) + ";" + \
        str(outputCursorCoordinateX) + ";" + \
        str(outputCursorCoordinateY) + ";" + \
        str(outputJoystickAxisX) + ";" + \
        str(outputJoystickAxisY) + ";" + \
        str(outputEnteredDigitsStr) + ";" + \
        str(outputEnteredDigitsLength) + ";" + \
        str(outputGeneratedTypingTaskNumbers) + ";" + \
        str(outputGeneratedTypingTaskNumbersLength) + ";" + \
        str(RuntimeVariables.NumberOfCircleExits) + ";" + \
        str(RuntimeVariables.TrialScore) + ";" + \
        str(RuntimeVariables.VisitScore) + ";" + \
        str(RuntimeVariables.CorrectlyTypedDigitsVisit) + ";" + \
        str(RuntimeVariables.IncorrectlyTypedDigitsVisit) + ";" + \
        str(RuntimeVariables.IncorrectlyTypedDigitsTrial) + ";" + \
        str(isCursorOutsideCircle()) + ";" + \
        str(RuntimeVariables.GainCorrectDigit) + ";" + \
        str(eventMessage1) + ";" + \
        str(eventMessage2) + "\n"

    if endOfTrial:
        RuntimeVariables.OutputDataFileTrialEnd.write(outputText)
        RuntimeVariables.OutputDataFileTrialEnd.flush()
        # typically the above line would do. however this is used to ensure that the file is written
        os.fsync(RuntimeVariables.OutputDataFileTrialEnd.fileno())

    RuntimeVariables.OutputDataFile.write(outputText)
    RuntimeVariables.OutputDataFile.flush()
    # typically the above line would do. however this is used to ensure that the file is written
    os.fsync(RuntimeVariables.OutputDataFile.fileno())


def quitApp(message=None):
    if message:
        print(message)
    RuntimeVariables.EnvironmentIsRunning = False
    pygame.display.quit()
    pygame.quit()
    try:
        if RuntimeVariables.OutputDataFile:
            RuntimeVariables.OutputDataFile.close()
        if RuntimeVariables.OutputDataFileTrialEnd:
            RuntimeVariables.OutputDataFileTrialEnd.close()
    except NameError:
        pass
    sys.exit()


def getFunctionName():
    return inspect.stack()[1][3]


def DrawGui():
    tkWindow = Tk()
    tkWindow.title(Constants.Title)

    ### Frames for input of Blocks consisting of tasks and trials
    frameLeft = Frame(tkWindow)
    frameLeft.grid(row=0, column=0)
    frameRight = Frame(tkWindow)
    frameRight.grid(row=0, column=1)

    frameBlocks = Frame(frameLeft, highlightbackground="black", highlightthickness=1)
    frameBlocks.grid(row=0, column=0)
    frameBlockListBox = Frame(frameBlocks)
    frameBlockListBox.grid(row=1, column=0)
    frameBlockButtons = Frame(frameBlocks)
    frameBlockButtons.grid(row=1, column=1)

    frameOptions = Frame(frameLeft, highlightbackground="black", highlightthickness=1)
    frameOptions.grid(row=1, column=0)

    frameBottom = Frame(frameLeft)
    frameBottom.grid(row=2, column=0)

    frameCircles = Frame(frameRight, highlightbackground="black", highlightthickness=1)
    frameCircles.grid(row=0, column=0)

    # Listbox and Delete button
    listBoxBlocks = Listbox(frameBlockListBox, width=25)
    listBoxBlocks.grid(row=0, column=0)
    btnDeleteBlock = Button(frameBlockListBox, text="Entfernen", command=lambda: listBoxBlocks.delete(listBoxBlocks.curselection()[0]))
    btnDeleteBlock.grid(row=1, column=0)

    # Blocks: Labels, Inputs and Buttons
    Label(frameBlocks, text="Eingabe von Blocks und Trials").grid(row=0, column=0)
    Label(frameBlockButtons, text="Anzahl Trials:").grid(row=0, column=0)
    txNumTrials = Text(frameBlockButtons, height=1, width=2)
    txNumTrials.grid(row=0, column=1)
    row = 1
    for btn in [("Übung Tracking", TaskTypes.PracticeSingleTracking), ("Übung Typing", TaskTypes.PracticeSingleTyping), ("Übung DualTask", TaskTypes.PracticeDualTask),
                ("Tracking", TaskTypes.SingleTracking), ("Typing", TaskTypes.SingleTyping), ("DualTask", TaskTypes.DualTask)]:
        btnDelete = Button(frameBlockButtons, text=btn[0], command=lambda btn=btn: CreateBlockListEntry(listBoxBlocks, buttonTitle=btn[0], taskType=btn[1], numTrials=txNumTrials.get("1.0", END)))
        btnDelete.grid(row=row, column=0)
        row += 1

    ### Create option checkboxes
    frameInputOptions = Frame(frameOptions)
    frameInputOptions.grid(row=0, column=0)
    Label(frameInputOptions, text="Probandennummer").grid(row=0, column=0)
    txPersonNumber = Text(frameInputOptions, height=1, width=2)
    txPersonNumber.grid(row=0, column=1)

    runPracticeTrials = IntVar()
    chkRunPracticeTrials = Checkbutton(frameOptions, text="Übungs-Trials durchführen", variable=runPracticeTrials)
    chkRunPracticeTrials.grid(row=1, column=0)
    showPenaltyRewardNoise = IntVar()
    chkShowPenaltyRewardNoise = Checkbutton(frameOptions, text="Penalty-Info vor dem Experiment anzeigen", variable=showPenaltyRewardNoise)
    chkShowPenaltyRewardNoise.grid(row=2, column=0)

    parallelDualTasks = IntVar()
    chkParallelDualTasks = Checkbutton(frameOptions, text="Parallele DualTasks", variable=parallelDualTasks)
    chkParallelDualTasks.grid(row=3, column=0)
    typingTaskInCursor = IntVar()
    chkTypingTaskInCursor = Checkbutton(frameOptions, text="Typing Task in Cursor", variable=typingTaskInCursor)
    chkTypingTaskInCursor.grid(row=4, column=0)

    disableTypingScoreOutside = IntVar()
    dtsoTxt = "Wenn sich im DualTask der Cursor ausserhalb des Kreises befindet,\n sollen im TypingTask korrekte Eingaben nicht gezählt werden"
    chkDisableTypingScoreOutside = Checkbutton(frameOptions, text=dtsoTxt, variable=disableTypingScoreOutside)
    chkDisableTypingScoreOutside.grid(row=5, column=0)

    ### Create three input forms for big, small and practice circles
    currentColumn = 0
    listBoxCirclesBig = Listbox()
    listBoxCirclesSmall = Listbox()
    listBoxCirclesPractice = Listbox()
    for circleType in [("circlePractice", "ÜBUNGS"), ("circleBig", "GROßE"), ("circleSmall", "KLEINE")]:
        circleIdentifier = circleType[0]
        circleTextWord = circleType[1]

        # Circle: Frames
        frameCircle = Frame(frameCircles, highlightbackground="black", highlightthickness=1)
        frameCircle.grid(row=currentColumn, column=0)
        frameCircleInputs = Frame(frameCircle)
        frameCircleInputs.grid(row=1, column=0)
        frameCirclesListBox = Frame(frameCircle)
        frameCirclesListBox.grid(row=1, column=1)
        frameCircleButtons = Frame(frameCircle)
        frameCircleButtons.grid(row=2, column=0)

        # Circles: Labels, Buttons and ListBox
        Label(frameCircle, text=f"Eingabe der Kreisradii für {circleTextWord} Kreise").grid(row=0, column=0)
        listBoxCircles = Listbox(frameCirclesListBox, width=100, height=10)
        listBoxCircles.grid(row=0, column=0)
        btnDeleteCircle = Button(frameCirclesListBox, text="Entfernen", command=lambda listBoxCircles=listBoxCircles: listBoxCircles.delete(listBoxCircles.curselection()[0]))
        btnDeleteCircle.grid(row=1, column=0)

        # Input fields for Circle attributes
        Label(frameCircleInputs, text="Radius:").grid(row=0, column=0)
        txRadiusInput = Text(frameCircleInputs, height=1, width=4)
        txRadiusInput.grid(row=0, column=1)
        Label(frameCircleInputs, text="Typing Task Ziffern:").grid(row=1, column=0)
        txTypingTaskNumbers = Text(frameCircleInputs, height=1, width=14)
        txTypingTaskNumbers.grid(row=1, column=1)
        Label(frameCircleInputs, text="Farbe Kreis innen (R,G,B):").grid(row=2, column=0)
        txInnerCircleColor = Text(frameCircleInputs, height=1, width=14)  # Enter a RGB color, e.g. (255, 0, 0) for Red
        txInnerCircleColor.grid(row=2, column=1)
        Label(frameCircleInputs, text="Farbe Kreis Rahmen (R,G,B):").grid(row=3, column=0)
        txBorderColor = Text(frameCircleInputs, height=1, width=14)
        txBorderColor.grid(row=3, column=1)
        currentColumn += 1
        btnAddCircle = Button(frameCircleInputs, text="Kreis hinzufügen",
                              command=lambda listBoxCircles=listBoxCircles, circleIdentifier=circleIdentifier, txRadiusInput=txRadiusInput, txTypingTaskNumbers=txTypingTaskNumbers, txInnerCircleColor=txInnerCircleColor, txBorderColor=txBorderColor:
                              CreateCircleListEntry(listBoxCircles, circleIdentifier, txRadiusInput.get("1.0", END), txTypingTaskNumbers.get("1.0", END), txInnerCircleColor.get("1.0", END), txBorderColor.get("1.0", END)))
        btnAddCircle.grid(row=4, column=0)

        # To load the circles from settings file, save the listboxes for later access
        if circleIdentifier == "circleBig":
            listBoxCirclesBig = listBoxCircles
        elif circleIdentifier == "circleSmall":
            listBoxCirclesSmall = listBoxCircles
        elif circleIdentifier == "circlePractice":
            listBoxCirclesPractice = listBoxCircles

    # Bottom Frame
    btnStart = Button(frameBottom, text="Starten",
                      command=lambda parallelDualTasks=parallelDualTasks,
                                     typingTaskInCursor=typingTaskInCursor,
                                     runPracticeTrials=runPracticeTrials,
                                     showPenaltyRewardNoise=showPenaltyRewardNoise:
                      ParseAndSaveInputs(tkWindow, listBoxBlocks, listBoxCirclesBig, listBoxCirclesSmall, listBoxCirclesPractice, txPersonNumber,
                                         parallelDualTasks, typingTaskInCursor, runPracticeTrials, showPenaltyRewardNoise, disableTypingScoreOutside))
    btnStart.grid(row=5, column=0)

    # Finally load settings from file if present
    settings = LoadSettingsFromFile()
    if settings:
        for block in settings.Blocks:
            CreateBlockListEntry(listBoxBlocks, buttonTitle=block[0], taskType=block[1], numTrials=block[2])
        for circle in settings.Circles:
            circleIdentifier = circle[0]
            if circleIdentifier == "circleBig":
                listBoxCircles = listBoxCirclesBig
            elif circleIdentifier == "circleSmall":
                listBoxCircles = listBoxCirclesSmall
            elif circleIdentifier == "circlePractice":
                listBoxCircles = listBoxCirclesPractice
            CreateCircleListEntry(listBoxCircles, circleType=circleIdentifier, radius=circle[1], typingTaskNumbers=circle[2], innerCircleColor=circle[3], borderColor=circle[4])
        for key, value in settings.Options.items():
            if key == "ParallelDualTasks" and value == "1":
                chkParallelDualTasks.select()
            if key == "DisplayTypingTaskWithinCursor" and value == "1":
                chkTypingTaskInCursor.select()
            if key == "RunPracticeTrials" and value == "1":
                chkRunPracticeTrials.select()
            if key == "ShowPenaltyRewardNoise" and value == "1":
                chkShowPenaltyRewardNoise.select()
            if key == "DisableTypingScoreOutside" and value == "1":
                chkDisableTypingScoreOutside.select()
    tkWindow.mainloop()


def CreateBlockListEntry(listBox, buttonTitle, taskType, numTrials):
    try:
        numTrialsParsed = int(numTrials)
    except ValueError:
        return
    if not numTrialsParsed > 0:
        return
    listBoxText = f"{buttonTitle}, {numTrialsParsed} Trial(s)"
    RuntimeVariables.DictTrialListEntries[listBoxText] = (buttonTitle, str(taskType), numTrialsParsed)
    listBox.insert(END, listBoxText)


def CreateCircleListEntry(listBox, circleType, radius, typingTaskNumbers, innerCircleColor, borderColor):
    try:
        radiusParsed = int(radius)
    except ValueError:
        return
    if not radiusParsed > 0:
        return
    circleType = circleType.strip()
    radius = radius.strip()
    typingTaskNumbers = typingTaskNumbers.strip()
    innerCircleColor = innerCircleColor.strip()  # RGB values are not validated for correctness yet
    borderColor = borderColor.strip()
    listBoxText = f"{circleType} Radius={radiusParsed}, DualTaskTypingNumbers={typingTaskNumbers}, InnerCircleColor={innerCircleColor}, BorderColor={borderColor}"
    if listBoxText in RuntimeVariables.DictTrialListEntries:
        raise Exception("Circle list entry is not unique")
    RuntimeVariables.DictTrialListEntries[listBoxText] = (circleType, radius, typingTaskNumbers, innerCircleColor, borderColor)
    listBox.insert(END, listBoxText)


class SettingsFile:
    Blocks = []
    Circles = []
    Options = {}


def LoadSettingsFromFile():
    if not path.exists(Constants.SettingsFilename):
        return
    csvFileContent = readCsvFile(Constants.SettingsFilename)
    settingsFile = SettingsFile()
    for line in csvFileContent:
        key = line[0]
        # Parse Blocks
        if key == "Block":
            buttonTitle = line[1]
            taskType = line[2]
            numTrials = line[3]
            settingsFile.Blocks.append((buttonTitle, taskType, numTrials))
        if key == "Circle":
            circleType = line[1]
            radius = line[2]
            typingTaskNumbers = line[3]
            innerCircleColor = line[4]
            borderColor = line[5]
            settingsFile.Circles.append((circleType, radius, typingTaskNumbers, innerCircleColor, borderColor))
        if key == "ParallelDualTasks":
            settingsFile.Options[key] = line[1]
        if key == "DisplayTypingTaskWithinCursor":
            settingsFile.Options[key] = line[1]
        if key == "RunPracticeTrials":
            settingsFile.Options[key] = line[1]
        if key == "ShowPenaltyRewardNoise":
            settingsFile.Options[key] = line[1]
        if key == "DisableTypingScoreOutside":
            settingsFile.Options[key] = line[1]
    return settingsFile


def ParseAndSaveInputs(tkWindow, listBoxBlocks, listBoxCirclesBig, listBoxCirclesSmall, listBoxCirclesPractice, txPersonNumber,
                       parallelDualTasks, typingTaskInCursor, runPracticeTrials, showPenaltyRewardNoise, disableTypingScoreOutside):
    linesSettingsFile = []
    # Write Blocks
    for listEntryText in listBoxBlocks.get(0, END):
        buttonTitle = RuntimeVariables.DictTrialListEntries[listEntryText][0]
        taskTypeUnparsed = RuntimeVariables.DictTrialListEntries[listEntryText][1]
        taskType = eval(taskTypeUnparsed)  # convert to Enum TaskTypes
        numTrials = int(RuntimeVariables.DictTrialListEntries[listEntryText][2])
        RuntimeVariables.RunningOrder.append(Block(taskType=taskType, numberOfTrials=numTrials))
        linesSettingsFile.append(["Block", buttonTitle, taskType, numTrials])
    # Write Circles
    listBoxCirclesEntries = listBoxCirclesBig.get(0, END) + listBoxCirclesSmall.get(0, END) + listBoxCirclesPractice.get(0, END)
    for listEntryText in listBoxCirclesEntries:
        circleType = RuntimeVariables.DictTrialListEntries[listEntryText][0]
        radius = int(RuntimeVariables.DictTrialListEntries[listEntryText][1])
        typingTaskNumbers = RuntimeVariables.DictTrialListEntries[listEntryText][2]
        innerCircleColor = eval(RuntimeVariables.DictTrialListEntries[listEntryText][3])
        borderColor = eval(RuntimeVariables.DictTrialListEntries[listEntryText][4])
        linesSettingsFile.append(["Circle", circleType, radius, typingTaskNumbers, innerCircleColor, borderColor])
        if circleType == "circleBig":
            RuntimeVariables.CirclesBig.append(Circle(radius, typingTaskNumbers, innerCircleColor, borderColor))
        elif circleType == "circleSmall":
            RuntimeVariables.CirclesSmall.append(Circle(radius, typingTaskNumbers, innerCircleColor, borderColor))
        elif circleType == "circlePractice":
            RuntimeVariables.CirclesPractice.append(Circle(radius, typingTaskNumbers, innerCircleColor, borderColor))

    try:
        RuntimeVariables.ParticipantNumber = str(int(txPersonNumber.get("1.0", END).strip()))
    except:
        print("No Subject number entered")
        return

    # Set Options to RuntimeVariables
    RuntimeVariables.ParallelDualTasks = True if parallelDualTasks.get() == 1 else False
    if typingTaskInCursor.get() == 1:
        RuntimeVariables.DisplayTypingTaskWithinCursor = True
        RuntimeVariables.ParallelDualTasks = True  # also required
    else:
        RuntimeVariables.DisplayTypingTaskWithinCursor = False

    RuntimeVariables.RunPracticeTrials = True if runPracticeTrials.get() == 1 else False
    RuntimeVariables.ShowPenaltyRewardNoise = True if showPenaltyRewardNoise.get() == 1 else False
    RuntimeVariables.DisableCorrectTypingScoreOutsideCircle = True if disableTypingScoreOutside.get() == 1 else False

    # Save Options to file
    linesSettingsFile.append(["ParallelDualTasks", parallelDualTasks.get()])
    linesSettingsFile.append(["DisplayTypingTaskWithinCursor", typingTaskInCursor.get()])
    linesSettingsFile.append(["RunPracticeTrials", runPracticeTrials.get()])
    linesSettingsFile.append(["ShowPenaltyRewardNoise", showPenaltyRewardNoise.get()])
    linesSettingsFile.append(["DisableTypingScoreOutside", disableTypingScoreOutside.get()])

    WriteLinesToCzvFile(Constants.SettingsFilename, linesSettingsFile)
    RuntimeVariables.EnvironmentIsRunning = True
    tkWindow.quit()


def WriteLinesToCzvFile(filename, lines):
    """Expectes lines to be a list of lists"""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(lines)


if __name__ == '__main__':
    try:
        DrawGui()
        if RuntimeVariables.EnvironmentIsRunning:  # check to avoid parsing incomplete form data on closing UI
            StartExperiment()
    except Exception as e:
        stack = traceback.format_exc()
        with open("Error_Logfile.txt", "a") as log:
            log.write(f"\n{datetime.datetime.now()} {str(e)}   {str(stack)} \n")
            print(str(e))
            print(str(stack))
            print("PLEASE CHECK Error_Logfile.txt, the error is logged there!")
